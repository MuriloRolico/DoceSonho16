# routes/order.py - VERSÃO CORRIGIDA

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session, current_app
import mercadopago
from database import db
from models.models import Pedido, ItemPedido, ItemPedidoPersonalizado, Produto, BoloPersonalizado, Usuario, CarrinhoItem, CarrinhoBoloPersonalizado
from utils.helpers import is_admin, registrar_log
from utils.payment import create_mercadopago_preference, create_mercadopago_preference_simple, create_mercadopago_preference_minimal
import json

order_bp = Blueprint('order', __name__)

# ROTA PARA FINALIZAR COMPRA - CORRIGIDA
# routes/order.py - Função finalizar_compra CORRIGIDA COMPLETA

@order_bp.route('/finalizar_compra', methods=['GET', 'POST'])
def finalizar_compra():
    if 'usuario_id' not in session:
        flash('Faça login para finalizar a compra!', 'danger')
        return redirect(url_for('auth.login'))
    
    # Buscar itens do carrinho do usuário
    usuario_id = session['usuario_id']
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        flash('Usuário não encontrado', 'danger')
        return redirect(url_for('auth.login'))
    
    # Itens regulares
    itens_regulares = []
    itens_db = CarrinhoItem.query.filter_by(usuario_id=usuario_id).all()
    subtotal_produtos = 0
    
    for item in itens_db:
        produto = Produto.query.get(item.produto_id)
        if produto:
            subtotal = produto.preco * item.quantidade
            subtotal_produtos += subtotal
            itens_regulares.append({
                'id': produto.id,
                'nome': produto.nome,
                'preco': produto.preco,
                'quantidade': item.quantidade,
                'subtotal': subtotal,
                'tipo': 'regular'
            })
    
    # Bolos personalizados
    itens_personalizados = []
    bolos_db = CarrinhoBoloPersonalizado.query.filter_by(usuario_id=usuario_id).all()
    
    for item in bolos_db:
        bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
        if bolo:
            subtotal = bolo.preco * item.quantidade
            subtotal_produtos += subtotal
            itens_personalizados.append({
                'id': bolo.id,
                'nome': f"Bolo Personalizado de {bolo.massa.capitalize()}",
                'preco': bolo.preco,
                'quantidade': item.quantidade,
                'subtotal': subtotal,
                'tipo': 'personalizado'
            })
    
    # Verificar se o carrinho está vazio
    tem_itens = len(itens_regulares) > 0 or len(itens_personalizados) > 0
    
    if not tem_itens:
        flash('Seu carrinho está vazio!', 'danger')
        return redirect(url_for('index'))
    
    # Combinar os dois tipos de itens
    todos_itens = itens_regulares + itens_personalizados
    
    # Renderizar a página com o formulário quando for GET
    if request.method == 'GET':
        return render_template('finalizar_compra.html', itens=todos_itens, total=subtotal_produtos, usuario=usuario)
    
    # PROCESSO POST - Processar o formulário
    if request.method == 'POST':
        try:
            # Obter tipo de entrega
            tipo_entrega = request.form.get('tipo_entrega')
            valor_frete = 0
            
            current_app.logger.info(f"=== PROCESSANDO FINALIZAR COMPRA ===")
            current_app.logger.info(f"Tipo de entrega selecionado: {tipo_entrega}")
            
            # Validar tipo de entrega
            if not tipo_entrega:
                flash('Por favor, selecione um tipo de entrega.', 'danger')
                return render_template('finalizar_compra.html', itens=todos_itens, total=subtotal_produtos, usuario=usuario)
            
            # Aplicar lógica de frete
            if tipo_entrega == 'frete':
                valor_frete = 12.00  # Valor do frete fixo
                current_app.logger.info(f"Taxa de entrega aplicada: R$ {valor_frete}")
                
                # Usar o endereço já cadastrado do usuário
                endereco_entrega = {
                    'rua': usuario.endereco_rua,
                    'numero': usuario.endereco_numero,
                    'complemento': usuario.endereco_complemento,
                    'bairro': usuario.endereco_bairro,
                    'cidade': usuario.endereco_cidade,
                    'estado': usuario.endereco_estado,
                    'cep': usuario.endereco_cep
                }
                
                # Verificar se o endereço está completo o suficiente para entrega
                if not endereco_entrega['rua'] or not endereco_entrega['cep'] or not endereco_entrega['bairro']:
                    flash('Para entrega, é necessário ter rua, CEP e bairro cadastrados. Por favor, atualize seu perfil.', 'warning')
                    return redirect(url_for('user.perfil'))
                    
            elif tipo_entrega == 'retirada':
                endereco_entrega = None
                current_app.logger.info("Retirada no local - sem taxa de entrega")
            else:
                # Valor não reconhecido
                flash('Tipo de entrega inválido. Tente novamente.', 'danger')
                return render_template('finalizar_compra.html', itens=todos_itens, total=subtotal_produtos, usuario=usuario)
            
            # Calcular total com frete
            total = subtotal_produtos + valor_frete
            current_app.logger.info(f"Total calculado: R$ {total:.2f} (Produtos: R$ {subtotal_produtos:.2f} + Frete: R$ {valor_frete:.2f})")
            
            # Validar se o total é válido
            if total <= 0:
                flash('Total do pedido inválido. Verifique os itens do carrinho.', 'danger')
                return redirect(url_for('cart.carrinho'))
            
            # SALVAR OS DADOS DO PEDIDO NA SESSÃO (não no banco ainda)
            session['pedido_temp'] = {
                'usuario_id': session['usuario_id'],
                'tipo_entrega': tipo_entrega,
                'valor_frete': valor_frete,
                'endereco_entrega': endereco_entrega,
                'observacoes': request.form.get('observacoes', ''),
                'total': total,
                'itens_regulares': [{'produto_id': item.produto_id, 'quantidade': item.quantidade} for item in itens_db],
                'itens_personalizados': [{'bolo_personalizado_id': item.bolo_personalizado_id, 'quantidade': item.quantidade} for item in bolos_db]
            }
            
            current_app.logger.info(f"Dados do pedido temporário salvos na sessão: {session['pedido_temp']}")
            
            # URLs de retorno após o pagamento - garantir que estejam absolutas e válidas
            base_url = request.host_url.rstrip('/')
            success_url = f"{base_url}{url_for('order.pagamento_sucesso')}"
            failure_url = f"{base_url}{url_for('order.pagamento_erro')}"
            pending_url = f"{base_url}{url_for('order.pagamento_pendente')}"
            
            # Log das URLs para verificação
            current_app.logger.info(f"URLs de retorno:")
            current_app.logger.info(f"Success: {success_url}")
            current_app.logger.info(f"Failure: {failure_url}")
            current_app.logger.info(f"Pending: {pending_url}")
            
            # Validar URLs antes de criar a preferência
            if not all([success_url, failure_url, pending_url]):
                current_app.logger.error("URLs de retorno inválidas")
                flash('Erro na configuração das URLs de retorno', 'danger')
                return redirect(url_for('cart.carrinho'))
            
            # Verificar se as URLs são válidas (não estão vazias e são URLs completas)
            for url_name, url_value in [('success', success_url), ('failure', failure_url), ('pending', pending_url)]:
                if not url_value or not url_value.startswith('http'):
                    current_app.logger.error(f"URL {url_name} inválida: {url_value}")
                    flash(f'Erro na configuração da URL de {url_name}', 'danger')
                    return redirect(url_for('cart.carrinho'))
            
            # IMPORTANTE: Configurar o delivery_option corretamente
            delivery_option = 'delivery' if tipo_entrega == 'frete' else 'pickup'
            current_app.logger.info(f"Delivery option configurado: {delivery_option}")
            
            # Tentar criar preferência de pagamento - usando as funções existentes
            payment_url = None
            error = None
            
            # 1ª tentativa: Usar a função principal (mais completa)
            current_app.logger.info("Tentativa 1: create_mercadopago_preference")
            payment_url, error = create_mercadopago_preference(
                session['usuario_id'], success_url, failure_url, pending_url, delivery_option
            )
            
            # 2ª tentativa: Usar a versão simplificada
            if not payment_url:
                current_app.logger.warning(f"Tentativa 1 falhou: {error}")
                current_app.logger.info("Tentativa 2: create_mercadopago_preference_simple")
                payment_url, error = create_mercadopago_preference_simple(
                    session['usuario_id'], success_url, failure_url, pending_url, delivery_option
                )
            
            # 3ª tentativa: Usar a versão minimalista
            if not payment_url:
                current_app.logger.warning(f"Tentativa 2 falhou: {error}")
                current_app.logger.info("Tentativa 3: create_mercadopago_preference_minimal")
                payment_url, error = create_mercadopago_preference_minimal(
                    session['usuario_id'], success_url, failure_url, pending_url, delivery_option
                )
            
            if payment_url:
                current_app.logger.info(f"Preferência criada com sucesso! Redirecionando para: {payment_url}")
                # Redirecionar para o Mercado Pago
                return redirect(payment_url)
            else:
                # Se houve erro na criação da preferência, limpar dados temporários
                session.pop('pedido_temp', None)
                current_app.logger.error(f"TODAS as tentativas falharam. Último erro: {error}")
                flash(f"Erro ao processar pagamento: {error}", 'danger')
                return redirect(url_for('cart.carrinho'))
                
        except Exception as e:
            # Se houve erro, limpar dados temporários
            session.pop('pedido_temp', None)
            current_app.logger.error(f"Erro ao processar pedido: {str(e)}")
            current_app.logger.error("Traceback:", exc_info=True)
            flash(f"Erro ao processar pagamento: {str(e)}", 'danger')
            return redirect(url_for('cart.carrinho'))
    
    # Fallback - nunca deveria chegar aqui, mas garantindo que sempre retorna algo
    return render_template('finalizar_compra.html', itens=todos_itens, total=subtotal_produtos, usuario=usuario)


# ROTA DE SUCESSO DO PAGAMENTO - CRIAR O PEDIDO APENAS AQUI
@order_bp.route('/pagamento/sucesso')
def pagamento_sucesso():
    try:
        # DEBUG: Log para verificar se a rota está sendo chamada
        current_app.logger.info("=== ROTA DE SUCESSO CHAMADA ===")
        current_app.logger.info(f"Session keys: {list(session.keys())}")
        
        # Verificar se existem dados temporários do pedido
        if 'pedido_temp' not in session:
            current_app.logger.error("pedido_temp não encontrado na session")
            current_app.logger.info(f"Session completa: {dict(session)}")
            flash('Dados do pedido não encontrados. Tente finalizar a compra novamente.', 'warning')
            return redirect(url_for('cart.carrinho'))
        
        pedido_temp = session['pedido_temp']
        current_app.logger.info(f"pedido_temp encontrado: {pedido_temp}")
        
        # Criar o pedido no banco de dados APENAS AGORA
        novo_pedido = Pedido(
            usuario_id=pedido_temp['usuario_id'],
            status='Aprovado',  # Já criamos como aprovado
            tipo_entrega=pedido_temp['tipo_entrega'],
             valor_frete=pedido_temp['valor_frete'],
            endereco_entrega=json.dumps(pedido_temp['endereco_entrega']) if pedido_temp['endereco_entrega'] else None,
            observacoes=pedido_temp['observacoes'],
            total=pedido_temp['total']
        )
        
        current_app.logger.info(f"Criando pedido: {novo_pedido.__dict__}")
        
        db.session.add(novo_pedido)
        db.session.flush()  # Para obter o ID do pedido
        
        current_app.logger.info(f"Pedido criado com ID: {novo_pedido.id}")
        
        itens_descricao = []
        
        # Adicionar itens regulares ao pedido
        for item_data in pedido_temp['itens_regulares']:
            current_app.logger.info(f"Processando item regular: {item_data}")
            produto = Produto.query.get(item_data['produto_id'])
            if produto:
                item_pedido = ItemPedido(
                    pedido_id=novo_pedido.id,
                    produto_id=produto.id,
                    quantidade=item_data['quantidade'],
                    preco_unitario=produto.preco
                )
                
                db.session.add(item_pedido)
                itens_descricao.append(f"{item_data['quantidade']}x {produto.nome}")
                current_app.logger.info(f"Item regular adicionado: {item_pedido.__dict__}")
        
        # Adicionar itens personalizados ao pedido
        for item_data in pedido_temp['itens_personalizados']:
            current_app.logger.info(f"Processando item personalizado: {item_data}")
            bolo = BoloPersonalizado.query.get(item_data['bolo_personalizado_id'])
            if bolo:
                item_pedido_personalizado = ItemPedidoPersonalizado(
                    pedido_id=novo_pedido.id,
                    bolo_personalizado_id=bolo.id,
                    quantidade=item_data['quantidade'],
                    preco_unitario=bolo.preco
                )
                
                db.session.add(item_pedido_personalizado)
                itens_descricao.append(f"{item_data['quantidade']}x Bolo personalizado de {bolo.massa.capitalize()}")
                current_app.logger.info(f"Item personalizado adicionado: {item_pedido_personalizado.__dict__}")
        
        # Limpar o carrinho após pagamento confirmado
        current_app.logger.info("Limpando carrinho...")
        CarrinhoItem.query.filter_by(usuario_id=pedido_temp['usuario_id']).delete()
        CarrinhoBoloPersonalizado.query.filter_by(usuario_id=pedido_temp['usuario_id']).delete()
        
        # Salvar tudo no banco
        current_app.logger.info("Fazendo commit no banco...")
        db.session.commit()
        current_app.logger.info("Commit realizado com sucesso!")
        
        # Limpar dados temporários da sessão
        session.pop('pedido_temp', None)
        
        # Registrar log
        descricao_log = f"Pedido #{novo_pedido.id} criado e aprovado com {len(itens_descricao)} itens: {', '.join(itens_descricao)}. Total: R$ {pedido_temp['total']:.2f}"
        if pedido_temp['valor_frete'] > 0:
            descricao_log += f" (inclui frete de R$ {pedido_temp['valor_frete']:.2f})"
        
        current_app.logger.info(f"Registrando log: {descricao_log}")
        
        registrar_log(
            tipo='pagamento_aprovado',
            descricao=descricao_log,
            usuario_id=session.get('usuario_id')
        )
        
        flash('Pagamento realizado com sucesso! Obrigado pela sua compra.', 'success')
        current_app.logger.info("=== SUCESSO PROCESSADO COM SUCESSO ===")
        
    except Exception as e:
        current_app.logger.error(f"ERRO ao processar confirmação de pagamento: {str(e)}")
        current_app.logger.error(f"Traceback: ", exc_info=True)
        db.session.rollback()
        # Limpar dados temporários em caso de erro
        session.pop('pedido_temp', None)
        flash('Erro ao processar confirmação de pagamento.', 'danger')
    
    return redirect(url_for('order.pedidos'))


# ROTAS DE ERRO E PENDENTE - LIMPAR DADOS TEMPORÁRIOS
@order_bp.route('/pagamento/erro')
def pagamento_erro():
    try:
        # Limpar dados temporários da sessão (não criar pedido)
        session.pop('pedido_temp', None)
        
        registrar_log(
            tipo='pagamento_erro',
            descricao="Pagamento rejeitado ou cancelado pelo usuário",
            usuario_id=session.get('usuario_id')
        )
        
        flash('Pagamento não foi aprovado. Tente novamente ou escolha outro método de pagamento.', 'warning')
        
    except Exception as e:
        current_app.logger.error(f"Erro ao processar falha de pagamento: {str(e)}")
        flash('Erro ao processar falha de pagamento.', 'danger')
    
    return redirect(url_for('cart.carrinho'))


@order_bp.route('/pagamento/pendente')
def pagamento_pendente():
    try:
        # Limpar dados temporários da sessão (não criar pedido)
        session.pop('pedido_temp', None)
        
        registrar_log(
            tipo='pagamento_pendente',
            descricao="Pagamento ficou pendente",
            usuario_id=session.get('usuario_id')
        )
        
        flash('Pagamento está pendente. Aguarde a confirmação ou tente novamente.', 'info')
        
    except Exception as e:
        current_app.logger.error(f"Erro ao processar pagamento pendente: {str(e)}")
        flash('Erro ao processar pagamento pendente.', 'danger')
    
    return redirect(url_for('cart.carrinho'))


# ROTA PARA LISTAR PEDIDOS DO USUÁRIO
@order_bp.route('/pedidos')
def pedidos():
    if 'usuario_id' not in session:
        flash('Faça login para ver seus pedidos!', 'danger')
        return redirect(url_for('auth.login'))
    
    usuario_id = session['usuario_id']
    
    # Buscar apenas pedidos aprovados (já que só criamos pedidos após confirmação)
    pedidos = Pedido.query.filter_by(usuario_id=usuario_id).order_by(Pedido.id.desc()).all()
    
    return render_template('pedidos.html', pedidos=pedidos)


# ROTA PARA VER DETALHES DE UM PEDIDO ESPECÍFICO - CORRIGIDA
@order_bp.route('/pedido/<int:pedido_id>')
def detalhes_pedido(pedido_id):
    if 'usuario_id' not in session:
        flash('Faça login para ver seus pedidos!', 'danger')
        return redirect(url_for('auth.login'))
    
    usuario_id = session['usuario_id']
    
    # Buscar o pedido, garantindo que pertence ao usuário logado
    pedido = Pedido.query.filter_by(id=pedido_id, usuario_id=usuario_id).first()
    
    if not pedido:
        flash('Pedido não encontrado ou você não tem permissão para visualizá-lo.', 'danger')
        return redirect(url_for('order.pedidos'))
    
    # Buscar itens regulares do pedido com informações do produto
    itens_regulares = db.session.query(
        ItemPedido.id,
        ItemPedido.quantidade,
        ItemPedido.preco_unitario,
        Produto.nome
    ).join(Produto).filter(ItemPedido.pedido_id == pedido.id).all()
    
    # Buscar itens personalizados do pedido com informações do bolo
    itens_personalizados = db.session.query(
        ItemPedidoPersonalizado.id,
        ItemPedidoPersonalizado.quantidade,
        ItemPedidoPersonalizado.preco_unitario,
        BoloPersonalizado.nome,
        BoloPersonalizado.id.label('bolo_id')
    ).join(BoloPersonalizado).filter(ItemPedidoPersonalizado.pedido_id == pedido.id).all()
    
    # Combinar os itens em uma única lista com todas as informações que o template precisa
    itens = []
    
    # Adicionar itens regulares
    for item in itens_regulares:
        itens.append({
            'id': item.id,
            'nome': item.nome,
            'quantidade': item.quantidade,
            'preco_unitario': item.preco_unitario,
            'subtotal': item.quantidade * item.preco_unitario,
            'tipo': 'regular',
            'bolo_id': None
        })
    
    # Adicionar itens personalizados
    for item in itens_personalizados:
        itens.append({
            'id': item.id,
            'nome': item.nome,
            'quantidade': item.quantidade,
            'preco_unitario': item.preco_unitario,
            'subtotal': item.quantidade * item.preco_unitario,
            'tipo': 'personalizado',
            'bolo_id': item.bolo_id
        })
    
    # Processar endereço de entrega se existir
    endereco_entrega = None
    if pedido.endereco_entrega:
        try:
            endereco_entrega = json.loads(pedido.endereco_entrega)
        except:
            endereco_entrega = None
    
    # Passar a lista unificada 'itens' para o template
    return render_template('detalhes_pedido.html', 
                         pedido=pedido, 
                         itens=itens,  # Lista unificada que o template espera
                         endereco_entrega=endereco_entrega)