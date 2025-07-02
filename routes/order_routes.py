from flask import Blueprint, render_template, request, redirect, url_for, flash, session , current_app
from database import db
from models.models import Pedido, ItemPedido, ItemPedidoPersonalizado, Produto, BoloPersonalizado, Usuario
from utils.helpers import is_admin, registrar_log
from utils.payment import create_mercadopago_preference

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
    
    tem_itens = ('carrinho' in session and session['carrinho']) or \
                ('carrinho_personalizado' in session and session['carrinho_personalizado'])
    
    if not tem_itens:
        flash('Seu carrinho está vazio!', 'danger')
        return redirect(url_for('index'))
    
    # Renderizar a página com o formulário quando for GET
    if request.method == 'GET':
        return render_template('finalizar_compra.html')
    
    if request.method == 'POST':
        # Criar novo pedido
        novo_pedido = Pedido(
            usuario_id=session['usuario_id'],
            status='Pendente'
        )
        
        db.session.add(novo_pedido)
        db.session.flush()  # Para obter o ID do pedido
        
        total = 0
        itens_descricao = []
        
        # Adicionar itens regulares ao pedido
        if 'carrinho' in session and session['carrinho']:
            for item_id, item in session['carrinho'].items():
                produto_id = item['id']
                quantidade = item['quantidade']
                preco = item['preco']
                subtotal = preco * quantidade
                total += subtotal
                
                item_pedido = ItemPedido(
                    pedido_id=novo_pedido.id,
                    produto_id=produto_id,
                    quantidade=quantidade,
                    preco_unitario=preco
                )
                
                db.session.add(item_pedido)
                
                # Adicionar à descrição para o log
                produto = Produto.query.get(produto_id)
                itens_descricao.append(f"{quantidade}x {produto.nome}")
        
        # Adicionar itens personalizados ao pedido
        if 'carrinho_personalizado' in session and session['carrinho_personalizado']:
            for item_id, item in session['carrinho_personalizado'].items():
                bolo_id = item['id']
                quantidade = item['quantidade']
                preco = item['preco']
                subtotal = preco * quantidade
                total += subtotal
                
                item_pedido_personalizado = ItemPedidoPersonalizado(
                    pedido_id=novo_pedido.id,
                    bolo_personalizado_id=bolo_id,
                    quantidade=quantidade,
                    preco_unitario=preco
                )
                
                db.session.add(item_pedido_personalizado)
                
                bolo = BoloPersonalizado.query.get(bolo_id)
                itens_descricao.append(f"{quantidade}x Bolo personalizado de {bolo.massa.capitalize()}")
        
        novo_pedido.total = total
        
        # Salvar no banco de dados
        db.session.commit()
        
        # Registrar o log de pedido
        descricao_log = f"Novo pedido #{novo_pedido.id} criado com {len(itens_descricao)} itens: {', '.join(itens_descricao)}. Total: R$ {total:.2f}"
        registrar_log(
            tipo='novo_pedido',
            descricao=descricao_log,
            usuario_id=session['usuario_id']
        )
        
        # URLs de retorno após o pagamento
        base_url = request.host_url.rstrip('/')
        success_url = f"{base_url}/pagamento/sucesso?pedido_id={novo_pedido.id}"
        failure_url = f"{base_url}/pagamento/erro?pedido_id={novo_pedido.id}"
        pending_url = f"{base_url}/pagamento/pendente?pedido_id={novo_pedido.id}"
        
        try:
            # Criar preferência de pagamento no Mercado Pago usando os itens da sessão
            payment_url, error = create_mercadopago_preference(
                session['usuario_id'], success_url, failure_url, pending_url
            )
            
            if payment_url:
                if 'carrinho' in session:
                    session.pop('carrinho')
                if 'carrinho_personalizado' in session:
                    session.pop('carrinho_personalizado')
                    
                return redirect(payment_url)  # Redireciona para o Mercado Pago
            else:
                flash(f"Erro ao processar pagamento: {error}", 'danger')
                return redirect(url_for('order.pedidos'))
        except Exception as e:
            flash(f"Erro ao processar pagamento: {str(e)}", 'danger')
            return redirect(url_for('order.pedidos'))

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