from flask import Blueprint, render_template, request, redirect, url_for, flash, session , current_app
from database import db
from models.models import Pedido, ItemPedido, ItemPedidoPersonalizado, Produto, BoloPersonalizado, Usuario, CarrinhoItem, CarrinhoBoloPersonalizado
from utils.helpers import is_admin, registrar_log
from utils.payment import create_mercadopago_preference, create_mercadopago_preference_simple
import json

order_bp = Blueprint('order', __name__)

@order_bp.route('/pedidos')
def pedidos():
    if 'usuario_id' not in session:
        flash('Faça login para ver seus pedidos!', 'danger')
        return redirect(url_for('auth.login'))
    
    usuario_pedidos = Pedido.query.filter_by(usuario_id=session['usuario_id']).order_by(Pedido.data.desc()).all()
    
    return render_template('pedidos.html', pedidos=usuario_pedidos)

@order_bp.route('/pedido/<int:pedido_id>')
def detalhes_pedido(pedido_id):
    if 'usuario_id' not in session:
        flash('Faça login para ver os detalhes do pedido!', 'danger')
        return redirect(url_for('auth.login'))
    
    pedido = Pedido.query.filter_by(id=pedido_id, usuario_id=session['usuario_id']).first_or_404()
    
    # Obter itens regulares
    itens_regulares = ItemPedido.query.filter_by(pedido_id=pedido.id).all()
    
    detalhes_itens_regulares = []
    for item in itens_regulares:
        produto = Produto.query.get(item.produto_id)
        detalhes_itens_regulares.append({
            'nome': produto.nome,
            'quantidade': item.quantidade,
            'preco_unitario': item.preco_unitario,
            'subtotal': item.preco_unitario * item.quantidade,
            'tipo': 'regular'
        })
    
    # Obter itens personalizados
    itens_personalizados = ItemPedidoPersonalizado.query.filter_by(pedido_id=pedido.id).all()
    
    detalhes_itens_personalizados = []
    for item in itens_personalizados:
        bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
        detalhes_itens_personalizados.append({
            'nome': f"Bolo Personalizado de {bolo.massa.capitalize()}",
            'quantidade': item.quantidade,
            'preco_unitario': item.preco_unitario,
            'subtotal': item.preco_unitario * item.quantidade,
            'tipo': 'personalizado',
            'bolo_id': bolo.id
        })
    
    # Combinar os dois tipos de itens
    todos_itens = detalhes_itens_regulares + detalhes_itens_personalizados
    
    return render_template('detalhes_pedido.html', pedido=pedido, itens=todos_itens)

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
        return render_template('finalizar_compra.html', itens=todos_itens, total=subtotal_produtos)
    
    if request.method == 'POST':
        # Obter tipo de entrega
        tipo_entrega = request.form.get('tipo_entrega')
        valor_frete = 0
        
        if tipo_entrega == 'frete':
            valor_frete = 12.00  # Valor do frete fixo
            
            # Usar o endereço já cadastrado do usuário
            endereco_entrega = {
                'rua': usuario.endereco_rua or '',
                'numero': usuario.endereco_numero or '',
                'complemento': usuario.endereco_complemento or '',
                'bairro': usuario.endereco_bairro or '',
                'cidade': usuario.endereco_cidade or '',
                'estado': usuario.endereco_estado or '',
                'cep': usuario.endereco_cep or ''
            }
            
            # Verificar se tem endereço cadastrado
            if not endereco_entrega['rua'] or not endereco_entrega['cep']:
                flash('Você não tem um endereço cadastrado completo. Por favor, atualize seu perfil.', 'danger')
                return redirect(url_for('user.perfil'))
        else:
            endereco_entrega = None
        
        # Calcular total com frete
        total = subtotal_produtos + valor_frete
        
        # Validar se o total é válido
        if total <= 0:
            flash('Total do pedido inválido. Verifique os itens do carrinho.', 'danger')
            return redirect(url_for('cart.carrinho'))
        
        # Criar novo pedido
        novo_pedido = Pedido(
            usuario_id=session['usuario_id'],
            status='Pendente',
            tipo_entrega=tipo_entrega,
            valor_frete=valor_frete,
            endereco_entrega=json.dumps(endereco_entrega) if endereco_entrega else None,
            observacoes=request.form.get('observacoes', ''),
            total=total
        )
        
        try:
            db.session.add(novo_pedido)
            db.session.flush()  # Para obter o ID do pedido
            
            itens_descricao = []
            
            # Adicionar itens regulares ao pedido
            for item in itens_db:
                produto = Produto.query.get(item.produto_id)
                if produto:
                    item_pedido = ItemPedido(
                        pedido_id=novo_pedido.id,
                        produto_id=produto.id,
                        quantidade=item.quantidade,
                        preco_unitario=produto.preco
                    )
                    
                    db.session.add(item_pedido)
                    itens_descricao.append(f"{item.quantidade}x {produto.nome}")
            
            # Adicionar itens personalizados ao pedido
            for item in bolos_db:
                bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
                if bolo:
                    item_pedido_personalizado = ItemPedidoPersonalizado(
                        pedido_id=novo_pedido.id,
                        bolo_personalizado_id=bolo.id,
                        quantidade=item.quantidade,
                        preco_unitario=bolo.preco
                    )
                    
                    db.session.add(item_pedido_personalizado)
                    itens_descricao.append(f"{item.quantidade}x Bolo personalizado de {bolo.massa.capitalize()}")
            
            # URLs de retorno após o pagamento - garantir que estejam absolutas e válidas
            base_url = request.host_url.rstrip('/')
            # Garantir que as URLs sejam absolutas e válidas
            success_url = f"{base_url}{url_for('order.pagamento_sucesso', pedido_id=novo_pedido.id)}"
            failure_url = f"{base_url}{url_for('order.pagamento_erro', pedido_id=novo_pedido.id)}"
            pending_url = f"{base_url}{url_for('order.pagamento_pendente', pedido_id=novo_pedido.id)}"
            
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
            
            # Log dos detalhes antes de criar a preferência
            current_app.logger.info(f"Criando preferência de pagamento para pedido {novo_pedido.id}")
            current_app.logger.info(f"Total: R$ {total:.2f}")
            current_app.logger.info(f"Itens: {itens_descricao}")
            
            # Criar preferência de pagamento com versão corrigida
            payment_url, error = create_mercadopago_preference_fixed(
                session['usuario_id'], success_url, failure_url, pending_url
            )
            
            # Se a versão corrigida não funcionar, tentar com outras versões
            if not payment_url:
                current_app.logger.warning(f"Versão corrigida falhou: {error}")
                payment_url, error = create_mercadopago_preference_simple(
                    session['usuario_id'], success_url, failure_url, pending_url
                )
            
            if not payment_url:
                current_app.logger.warning(f"Versão simplificada falhou: {error}")
                payment_url, error = create_mercadopago_preference(
                    session['usuario_id'], success_url, failure_url, pending_url
                )
            
            if payment_url:
                # Só limpar o carrinho DEPOIS de criar a preferência com sucesso
                CarrinhoItem.query.filter_by(usuario_id=usuario_id).delete()
                CarrinhoBoloPersonalizado.query.filter_by(usuario_id=usuario_id).delete()
                
                # Salvar no banco de dados
                db.session.commit()
                
                # Registrar o log de pedido
                descricao_log = f"Novo pedido #{novo_pedido.id} criado com {len(itens_descricao)} itens: {', '.join(itens_descricao)}. Total: R$ {total:.2f} (incluindo frete de R$ {valor_frete:.2f})"
                registrar_log(
                    tipo='novo_pedido',
                    descricao=descricao_log,
                    usuario_id=session['usuario_id']
                )
                
                current_app.logger.info(f"Redirecionando para pagamento: {payment_url}")
                
                # Redirecionar para o Mercado Pago
                return redirect(payment_url)
            else:
                # Se houve erro na criação da preferência, fazer rollback
                db.session.rollback()
                current_app.logger.error(f"Erro ao criar preferência de pagamento: {error}")
                flash(f"Erro ao processar pagamento: {error}", 'danger')
                return redirect(url_for('order.pedidos'))
                
        except Exception as e:
            # Se houve erro, fazer rollback
            db.session.rollback()
            current_app.logger.error(f"Erro ao processar pedido: {str(e)}")
            flash(f"Erro ao processar pagamento: {str(e)}", 'danger')
            return redirect(url_for('cart.carrinho'))

def create_mercadopago_preference_fixed(user_id, success_url, failure_url, pending_url):
    """
    Versão corrigida da função de criação de preferência do MercadoPago
    com foco em resolver o erro de auto_return e URLs inválidas.
    """
    try:
        # Importar aqui para evitar imports circulares
        from models.models import CarrinhoItem, CarrinhoBoloPersonalizado, Produto, BoloPersonalizado
        import mercadopago
        
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
                        'title': produto.nome[:256],  # Limitar tamanho
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
                        'title': f"Bolo Personalizado - {bolo.massa}"[:256],
                        'quantity': int(item.quantidade),
                        'unit_price': float(bolo.preco),
                        'currency_id': 'BRL'
                    })
        
        if not items:
            return None, "Carrinho vazio"
        
        # Validar URLs - garantir que todas sejam absolutas e válidas
        for url_name, url_value in [('success', success_url), ('failure', failure_url), ('pending', pending_url)]:
            if not url_value or not url_value.startswith('http'):
                return None, f"URL {url_name} inválida: {url_value}"
        
        # Configurar SDK
        access_token = current_app.config.get('MERCADO_PAGO_ACCESS_TOKEN') or "APP_USR-3186829371371378-033109-bd70da5615618f6121a56627b441334a-2363984332"
        sdk = mercadopago.SDK(access_token)
        
        # Dados da preferência CORRIGIDOS
        preference_data = {
            "items": items,
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            },
            # REMOVIDO o auto_return que estava causando o erro
            "external_reference": str(user_id) if user_id else "guest",
            "statement_descriptor": "DOCE SONHO",
            "expires": False,
            "payment_methods": {
                "installments": 12
            }
        }
        
        # Adicionar notification_url se disponível
        notification_url = current_app.config.get('MERCADO_PAGO_NOTIFICATION_URL')
        if notification_url:
            preference_data["notification_url"] = notification_url
        
        current_app.logger.info(f"Criando preferência CORRIGIDA com dados: {preference_data}")
        
        # Criar preferência
        result = sdk.preference().create(preference_data)
        
        current_app.logger.info(f"Resultado da criação CORRIGIDA: {result}")
        
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
        current_app.logger.error(f"Erro na criação da preferência CORRIGIDA: {str(e)}")
        return None, f"Erro interno: {str(e)}"

@order_bp.route('/pagamento/sucesso')
def pagamento_sucesso():
    pedido_id = request.args.get('pedido_id')
    if pedido_id:
        pedido = Pedido.query.get(pedido_id)
        if pedido:
            pedido.status = 'Aprovado'
            db.session.commit()
            
            registrar_log(
                tipo='pagamento_aprovado',
                descricao=f"Pagamento aprovado para o pedido #{pedido_id}",
                usuario_id=session.get('usuario_id')
            )
            
    flash('Pagamento realizado com sucesso! Obrigado pela sua compra.', 'success')
    return redirect(url_for('order.pedidos'))

@order_bp.route('/pagamento/pendente')
def pagamento_pendente():
    pedido_id = request.args.get('pedido_id')
    if pedido_id:
        pedido = Pedido.query.get(pedido_id)
        if pedido:
            pedido.status = 'Aguardando Pagamento'
            db.session.commit()
            
            registrar_log(
                tipo='pagamento_pendente',
                descricao=f"Pagamento pendente para o pedido #{pedido_id}",
                usuario_id=session.get('usuario_id')
            )
    
    flash('Seu pagamento está sendo processado. Você receberá uma confirmação em breve.', 'info')
    return redirect(url_for('order.pedidos'))

@order_bp.route('/pagamento/erro')
def pagamento_erro():
    pedido_id = request.args.get('pedido_id')
    if pedido_id:
        registrar_log(
            tipo='pagamento_erro',
            descricao=f"Erro no pagamento para o pedido #{pedido_id}",
            usuario_id=session.get('usuario_id')
        )
    
    flash('Houve um problema com seu pagamento. Por favor, tente novamente ou entre em contato conosco.', 'danger')
    return redirect(url_for('order.pedidos'))