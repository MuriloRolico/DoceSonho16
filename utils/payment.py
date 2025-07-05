import mysql.connector
import mercadopago
from decimal import Decimal
from flask import session, current_app
from models.models import Produto, BoloPersonalizado, CarrinhoItem, CarrinhoBoloPersonalizado
from database import db
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mercadopago_preference(user_id, success_url, failure_url, pending_url):
    """
    Cria uma preferência de pagamento no MercadoPago com base nos itens do carrinho.
    
    Args:
        user_id: ID do usuário
        success_url: URL de retorno em caso de sucesso
        failure_url: URL de retorno em caso de falha
        pending_url: URL de retorno em caso de pagamento pendente
        
    Returns:
        Tupla (link_pagamento, erro) - link de pagamento do MercadoPago ou None em caso de erro
    """
    items = []
    
    try:
        # Se usuário estiver logado, buscar itens do banco de dados
        if user_id:
            # Buscar produtos regulares
            itens_regulares = CarrinhoItem.query.filter_by(usuario_id=user_id).all()
            for item in itens_regulares:
                produto = Produto.query.get(item.produto_id)
                if produto:
                    # Validar dados antes de adicionar
                    if produto.preco <= 0:
                        logger.warning(f"Produto {produto.id} tem preço inválido: {produto.preco}")
                        continue
                    
                    items.append({
                        'id': str(produto.id),
                        'title': produto.nome[:256],  # Limitar tamanho do título
                        'description': (produto.descricao or 'Produto da Doce Sonho')[:256],
                        'quantity': int(item.quantidade),
                        'unit_price': float(produto.preco),
                        'currency_id': 'BRL'
                    })
            
            # Buscar bolos personalizados
            bolos_personalizados = CarrinhoBoloPersonalizado.query.filter_by(usuario_id=user_id).all()
            for item in bolos_personalizados:
                bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
                if bolo:
                    # Validar dados antes de adicionar
                    if bolo.preco <= 0:
                        logger.warning(f"Bolo personalizado {bolo.id} tem preço inválido: {bolo.preco}")
                        continue
                    
                    descricao = f"Massa: {bolo.massa.capitalize()}"
                    if bolo.recheios:
                        descricao += f", Recheios: {bolo.recheios}"
                    if bolo.cobertura:
                        descricao += f", Cobertura: {bolo.cobertura}"
                    
                    items.append({
                        'id': str(bolo.id),
                        'title': 'Bolo Personalizado',
                        'description': descricao[:256],  # Limitar tamanho da descrição
                        'quantity': int(item.quantidade),
                        'unit_price': float(bolo.preco),
                        'currency_id': 'BRL'
                    })
        else:
            # Buscar itens da sessão (usuário não logado)
            if 'carrinho' in session and session['carrinho']:
                for item_id, item in session['carrinho'].items():
                    if item['preco'] <= 0:
                        logger.warning(f"Item da sessão {item_id} tem preço inválido: {item['preco']}")
                        continue
                    
                    items.append({
                        'id': str(item['id']),
                        'title': item['nome'][:256],
                        'description': item.get('descricao', 'Produto da Doce Sonho')[:256],
                        'quantity': int(item['quantidade']),
                        'unit_price': float(item['preco']),
                        'currency_id': 'BRL'
                    })
            
            if 'carrinho_personalizado' in session and session['carrinho_personalizado']:
                for item_id, item in session['carrinho_personalizado'].items():
                    if item['preco'] <= 0:
                        logger.warning(f"Bolo personalizado da sessão {item_id} tem preço inválido: {item['preco']}")
                        continue
                    
                    descricao = f"Massa: {item.get('massa', '').capitalize()}"
                    if 'recheios' in item:
                        descricao += f", Recheios: {item['recheios']}"
                    if 'cobertura' in item:
                        descricao += f", Cobertura: {item['cobertura']}"
                        
                    items.append({
                        'id': str(item['id']),
                        'title': 'Bolo Personalizado',
                        'description': descricao[:256],
                        'quantity': int(item['quantidade']),
                        'unit_price': float(item['preco']),
                        'currency_id': 'BRL'
                    })
        
        if not items:
            return None, "Não há itens no carrinho"
        
        # Log dos itens para debug
        logger.info(f"Itens para pagamento: {items}")
        logger.info(f"URLs de retorno - Success: {success_url}, Failure: {failure_url}, Pending: {pending_url}")
        
        # Validar URLs antes de criar a preferência
        if not success_url or not failure_url or not pending_url:
            return None, "URLs de retorno não foram definidas corretamente"
        
        # Configurar SDK do MercadoPago
        # IMPORTANTE: Substitua pelo seu token de acesso real
        access_token = current_app.config.get('MERCADO_PAGO_ACCESS_TOKEN') or "APP_USR-3186829371371378-033109-bd70da5615618f6121a56627b441334a-2363984332"
        sdk = mercadopago.SDK(access_token)
        
        # Criar preferência de pagamento
        preference_data = {
            "items": items,
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            },
            # CORRIGIDO: Removendo auto_return ou definindo como "all"
            "auto_return": "all",
            "external_reference": str(user_id) if user_id else "guest",
            "statement_descriptor": "DOCE SONHO",
            "expires": False,
            "payment_methods": {
                "excluded_payment_types": [],
                "installments": 12
            },
            # Adicionando notification_url se disponível
            "notification_url": current_app.config.get('MERCADO_PAGO_NOTIFICATION_URL')
        }
        
        # Remover notification_url se não estiver configurado
        if not preference_data["notification_url"]:
            preference_data.pop("notification_url", None)
        
        logger.info(f"Dados da preferência: {preference_data}")
        
        preference_response = sdk.preference().create(preference_data)
        
        # Log da resposta completa para debug
        logger.info(f"Resposta do Mercado Pago: {preference_response}")
        
        # Verificar se houve erro na resposta
        if preference_response.get("status") != 201:
            error_msg = f"Erro na API do Mercado Pago. Status: {preference_response.get('status')}"
            if "response" in preference_response:
                if "message" in preference_response["response"]:
                    error_msg += f". Mensagem: {preference_response['response']['message']}"
                if "cause" in preference_response["response"]:
                    error_msg += f". Causa: {preference_response['response']['cause']}"
            logger.error(error_msg)
            return None, error_msg
        
        preference = preference_response["response"]
        
        # Verificar se o init_point existe
        if "init_point" in preference:
            logger.info(f"Link de pagamento criado com sucesso: {preference['init_point']}")
            return preference["init_point"], None
        elif "sandbox_init_point" in preference:
            # Em ambiente de testes, usar sandbox_init_point
            logger.info(f"Link de pagamento sandbox criado: {preference['sandbox_init_point']}")
            return preference["sandbox_init_point"], None
        else:
            logger.error(f"Resposta não contém init_point: {preference}")
            return None, "Não foi possível obter o link de pagamento"
    
    except Exception as e:
        logger.error(f"Erro ao criar preferência de pagamento: {str(e)}")
        return None, f"Erro ao criar preferência de pagamento: {str(e)}"


def create_mercadopago_preference_simple(user_id, success_url, failure_url, pending_url):
    """
    Versão simplificada e mais robusta da função de criação de preferência.
    """
    try:
        # Buscar itens do carrinho
        items = []
        
        if user_id:
            # Produtos regulares
            itens_regulares = CarrinhoItem.query.filter_by(usuario_id=user_id).all()
            for item in itens_regulares:
                produto = Produto.query.get(item.produto_id)
                if produto and produto.preco > 0:
                    items.append({
                        'id': str(produto.id),
                        'title': produto.nome[:256],  # Limitar tamanho do título
                        'quantity': int(item.quantidade),
                        'unit_price': float(produto.preco),
                        'currency_id': 'BRL'
                    })
            
            # Bolos personalizados
            bolos_personalizados = CarrinhoBoloPersonalizado.query.filter_by(usuario_id=user_id).all()
            for item in bolos_personalizados:
                bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
                if bolo and bolo.preco > 0:
                    items.append({
                        'id': f"bolo_{bolo.id}",
                        'title': f"Bolo Personalizado - {bolo.massa}",
                        'quantity': int(item.quantidade),
                        'unit_price': float(bolo.preco),
                        'currency_id': 'BRL'
                    })
        
        if not items:
            return None, "Carrinho vazio"
        
        # Validar URLs - garantir que todas estejam presentes
        if not all([success_url, failure_url, pending_url]):
            return None, "URLs de retorno inválidas"
        
        # Configurar SDK
        sdk = mercadopago.SDK("APP_USR-3186829371371378-033109-bd70da5615618f6121a56627b441334a-2363984332")
        
        # Dados da preferência (versão mais simples e corrigida)
        preference_data = {
            "items": items,
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            },
            # CORRIGIDO: Usando "all" para funcionar com todas as URLs
            "auto_return": "all",
            "external_reference": str(user_id) if user_id else "guest",
            "statement_descriptor": "DOCE SONHO"
        }
        
        logger.info(f"Criando preferência com dados: {preference_data}")
        
        # Criar preferência
        result = sdk.preference().create(preference_data)
        
        logger.info(f"Resultado da criação: {result}")
        
        if result["status"] == 201:
            preference = result["response"]
            init_point = preference.get("init_point") or preference.get("sandbox_init_point")
            
            if init_point:
                return init_point, None
            else:
                return None, "Link de pagamento não encontrado na resposta"
        else:
            error_msg = "Erro desconhecido"
            if "response" in result:
                if "message" in result["response"]:
                    error_msg = result["response"]["message"]
                elif "cause" in result["response"]:
                    error_msg = result["response"]["cause"]
            return None, f"Erro {result['status']}: {error_msg}"
            
    except Exception as e:
        logger.error(f"Erro na criação da preferência: {str(e)}")
        return None, f"Erro interno: {str(e)}"


def validate_mercadopago_config():
    """
    Valida se a configuração do Mercado Pago está correta.
    
    Returns:
        Tuple (is_valid, error_message)
    """
    try:
        access_token = current_app.config.get('MERCADO_PAGO_ACCESS_TOKEN') or "APP_USR-3186829371371378-033109-bd70da5615618f6121a56627b441334a-2363984332"
        sdk = mercadopago.SDK(access_token)
        
        # Testar conectividade com uma requisição simples
        response = sdk.preference().search()
        
        if response.get("status") == 200:
            return True, None
        else:
            return False, f"Erro na configuração do Mercado Pago: {response.get('status')}"
    
    except Exception as e:
        return False, f"Erro ao validar configuração do Mercado Pago: {str(e)}"


def create_mercadopago_preference_minimal(user_id, success_url, failure_url, pending_url):
    """
    Versão minimalista para testes - apenas com campos obrigatórios.
    """
    try:
        # Buscar itens do carrinho
        items = []
        
        if user_id:
            # Produtos regulares
            itens_regulares = CarrinhoItem.query.filter_by(usuario_id=user_id).all()
            for item in itens_regulares:
                produto = Produto.query.get(item.produto_id)
                if produto and produto.preco > 0:
                    items.append({
                        'title': produto.nome[:256],
                        'quantity': int(item.quantidade),
                        'unit_price': float(produto.preco),
                        'currency_id': 'BRL'
                    })
            
            # Bolos personalizados
            bolos_personalizados = CarrinhoBoloPersonalizado.query.filter_by(usuario_id=user_id).all()
            for item in bolos_personalizados:
                bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
                if bolo and bolo.preco > 0:
                    items.append({
                        'title': f"Bolo Personalizado - {bolo.massa}",
                        'quantity': int(item.quantidade),
                        'unit_price': float(bolo.preco),
                        'currency_id': 'BRL'
                    })
        
        if not items:
            return None, "Carrinho vazio"
        
        # Configurar SDK
        sdk = mercadopago.SDK("APP_USR-3186829371371378-033109-bd70da5615618f6121a56627b441334a-2363984332")
        
        # Dados da preferência minimalista
        preference_data = {
            "items": items,
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            }
        }
        
        logger.info(f"Criando preferência minimalista: {preference_data}")
        
        # Criar preferência
        result = sdk.preference().create(preference_data)
        
        logger.info(f"Resultado da criação minimalista: {result}")
        
        if result["status"] == 201:
            preference = result["response"]
            init_point = preference.get("init_point") or preference.get("sandbox_init_point")
            
            if init_point:
                return init_point, None
            else:
                return None, "Link de pagamento não encontrado na resposta"
        else:
            error_msg = "Erro desconhecido"
            if "response" in result:
                if "message" in result["response"]:
                    error_msg = result["response"]["message"]
                elif "cause" in result["response"]:
                    error_msg = result["response"]["cause"]
            return None, f"Erro {result['status']}: {error_msg}"
            
    except Exception as e:
        logger.error(f"Erro na criação da preferência minimalista: {str(e)}")
        return None, f"Erro interno: {str(e)}"