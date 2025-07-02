from flask import Blueprint, render_template, request, redirect, url_for, flash, session , current_app
from database import db
from models.models import Produto, BoloPersonalizado, Usuario

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/carrinho')
def carrinho():
    # Inicializar variáveis
    itens_regulares = []
    itens_personalizados = []
    total = 0
    
    if 'carrinho' in session and session['carrinho']:
        for item in session['carrinho'].values():
            subtotal = item['preco'] * item['quantidade']
            total += subtotal
            itens_regulares.append({
                'id': item['id'],
                'nome': item['nome'],
                'preco': item['preco'],
                'quantidade': item['quantidade'],
                'subtotal': subtotal,
                'tipo': 'regular'
            })
    
    if 'carrinho_personalizado' in session and session['carrinho_personalizado']:
        for item in session['carrinho_personalizado'].values():
            subtotal = item['preco'] * item['quantidade']
            total += subtotal
            itens_personalizados.append({
                'id': item['id'],
                'nome': item['nome'],
                'preco': item['preco'],
                'quantidade': item['quantidade'],
                'subtotal': subtotal,
                'tipo': 'personalizado'
            })
    
    # Combinar os dois tipos de itens
    todos_itens = itens_regulares + itens_personalizados
    
    return render_template('carrinho.html', itens=todos_itens, total=total)

@cart_bp.route('/adicionar_ao_carrinho/<int:produto_id>')
def adicionar_ao_carrinho(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    
    if 'carrinho' not in session:
        session['carrinho'] = {}
    
    carrinho = session['carrinho']
    
    produto_id_str = str(produto_id)
    
    if produto_id_str in carrinho:
        carrinho[produto_id_str]['quantidade'] += 1
    else:
        carrinho[produto_id_str] = {
            'id': produto_id,
            'nome': produto.nome,
            'preco': produto.preco,
            'quantidade': 1
        }
    
    session['carrinho'] = carrinho
    flash(f'{produto.nome} adicionado ao carrinho!', 'success')
    return redirect(url_for('index'))

@cart_bp.route('/bolo-personalizado/<int:bolo_id>/adicionar')
def adicionar_bolo_personalizado_ao_carrinho(bolo_id):
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para adicionar este item ao carrinho', 'warning')
        return redirect(url_for('auth.login'))
    
    bolo = BoloPersonalizado.query.get_or_404(bolo_id)
    
    # Verificar se o bolo pertence ao usuário
    if bolo.usuario_id != session['usuario_id']:
        flash('Você não tem permissão para adicionar este bolo ao carrinho', 'danger')
        return redirect(url_for('index'))
    
    if 'carrinho_personalizado' not in session:
        session['carrinho_personalizado'] = {}
    
    carrinho_personalizado = session['carrinho_personalizado']
    bolo_id_str = str(bolo_id)
    
    if bolo_id_str in carrinho_personalizado:
        carrinho_personalizado[bolo_id_str]['quantidade'] += 1
    else:
        carrinho_personalizado[bolo_id_str] = {
            'id': bolo_id,
            'nome': f"Bolo Personalizado de {bolo.massa.capitalize()}",
            'preco': bolo.preco,
            'quantidade': 1
        }
    
    session['carrinho_personalizado'] = carrinho_personalizado
    flash(f'Bolo personalizado adicionado ao carrinho!', 'success')
    return redirect(url_for('cart.carrinho'))

@cart_bp.route('/remover_do_carrinho/<int:produto_id>')
def remover_do_carrinho(produto_id):
    if 'carrinho' in session:
        produto_id_str = str(produto_id)
        if produto_id_str in session['carrinho']:
            del session['carrinho'][produto_id_str]
            session.modified = True
            flash('Item removido do carrinho!', 'success')
    
    return redirect(url_for('cart.carrinho'))

@cart_bp.route('/remover_bolo_personalizado/<int:bolo_id>')
def remover_bolo_personalizado(bolo_id):
    if 'carrinho_personalizado' in session:
        bolo_id_str = str(bolo_id)
        if bolo_id_str in session['carrinho_personalizado']:
            del session['carrinho_personalizado'][bolo_id_str]
            session.modified = True
            flash('Bolo personalizado removido do carrinho!', 'success')
    
    return redirect(url_for('cart.carrinho'))

@cart_bp.route('/atualizar_carrinho', methods=['POST'])
def atualizar_carrinho():
    # Atualizar carrinho regular
    if 'carrinho' in session:
        carrinho = session['carrinho']
        
        for produto_id, quantidade in request.form.items():
            if produto_id.startswith('quantidade_regular_'):
                produto_id_real = produto_id.replace('quantidade_regular_', '')
                try:
                    nova_quantidade = int(quantidade)
                    if nova_quantidade > 0 and produto_id_real in carrinho:
                        carrinho[produto_id_real]['quantidade'] = nova_quantidade
                except ValueError:
                    pass
        
        session['carrinho'] = carrinho
    
    # Atualizar carrinho personalizado
    if 'carrinho_personalizado' in session:
        carrinho_personalizado = session['carrinho_personalizado']
        
        for bolo_id, quantidade in request.form.items():
            if bolo_id.startswith('quantidade_personalizado_'):
                bolo_id_real = bolo_id.replace('quantidade_personalizado_', '')
                try:
                    nova_quantidade = int(quantidade)
                    if nova_quantidade > 0 and bolo_id_real in carrinho_personalizado:
                        carrinho_personalizado[bolo_id_real]['quantidade'] = nova_quantidade
                except ValueError:
                    pass
        
        session['carrinho_personalizado'] = carrinho_personalizado
    
    flash('Carrinho atualizado com sucesso!', 'success')
    return redirect(url_for('cart.carrinho'))