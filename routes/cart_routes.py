from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from database import db
from models.models import Produto, BoloPersonalizado, Usuario, CarrinhoItem, CarrinhoBoloPersonalizado
from utils.helpers import registrar_log
import json

cart_bp = Blueprint('cart', __name__)

def formatar_lista_json(valor):
    """
    Converte uma string JSON para uma lista formatada e legível
    """
    if not valor:
        return ""
    
    try:
        # Se já é uma lista, usa diretamente
        if isinstance(valor, list):
            lista = valor
        else:
            # Tenta fazer parse do JSON
            lista = json.loads(valor)
        
        # Formata os itens da lista
        itens_formatados = []
        for item in lista:
            # Remove underscores e capitaliza
            item_formatado = item.replace('_', ' ').title()
            itens_formatados.append(item_formatado)
        
        return ', '.join(itens_formatados)
    except:
        # Se não conseguir fazer parse, tenta tratar como string simples
        return valor.replace('_', ' ').title() if valor else ""

def formatar_campo_simples(valor):

    if not valor:
        return ""
    return valor.replace('_', ' ').title()

@cart_bp.route('/carrinho')
def carrinho():
    # Inicializar variáveis
    itens_regulares = []
    itens_personalizados = []
    total = 0
    
    # Verificar se o usuário está logado para recuperar carrinho persistente
    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        # Buscar itens regulares do banco de dados
        itens_db = CarrinhoItem.query.filter_by(usuario_id=usuario_id).all()
        for item in itens_db:
            produto = Produto.query.get(item.produto_id)
            if produto:
                subtotal = produto.preco * item.quantidade
                total += subtotal
                itens_regulares.append({
                    'id': produto.id,
                    'nome': produto.nome,
                    'preco': produto.preco,
                    'quantidade': item.quantidade,
                    'subtotal': subtotal,
                    'tipo': 'regular'
                })
        
        # Buscar bolos personalizados do banco de dados
        bolos_db = CarrinhoBoloPersonalizado.query.filter_by(usuario_id=usuario_id).all()
        for item in bolos_db:
            bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
            if bolo:
                subtotal = bolo.preco * item.quantidade
                total += subtotal
                itens_personalizados.append({
                    'id': bolo.id,
                    'nome': bolo.nome or f"Bolo Personalizado de {formatar_campo_simples(bolo.massa) if bolo.massa else 'Personalizado'}",
                    'massa': formatar_campo_simples(bolo.massa),
                    'recheios': formatar_lista_json(bolo.recheios),
                    'cobertura': formatar_campo_simples(bolo.cobertura),
                    'finalizacao': formatar_lista_json(bolo.finalizacao),
                    'observacoes': bolo.observacoes,
                    'preco': bolo.preco,
                    'quantidade': item.quantidade,
                    'subtotal': subtotal,
                    'tipo': 'personalizado'
                })
    else:
        
        # Manter a funcionalidade do carrinho na sessão para usuários não logados
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
                    'massa': formatar_campo_simples(item.get('massa', '')),
                    'recheios': formatar_lista_json(item.get('recheios', '')),
                    'cobertura': formatar_campo_simples(item.get('cobertura', '')),
                    'finalizacao': formatar_lista_json(item.get('finalizacao', '')),
                    'observacoes': item.get('observacoes', ''),
                    'preco': item['preco'],
                    'quantidade': item['quantidade'],
                    'subtotal': subtotal,
                    'tipo': 'personalizado'
                })
    
    # Combinar os dois tipos de itens
    todos_itens = itens_regulares + itens_personalizados
    
    return render_template('carrinho.html', itens=todos_itens, total=total)

@cart_bp.route('/adicionar/<int:produto_id>')
def adicionar_ao_carrinho(produto_id):
    # Verificar se produto existe e está ativo
    produto = Produto.query.filter_by(id=produto_id, ativo=True).first_or_404()
    # resto do código...
    
    # Se o usuário estiver logado, salvar no banco de dados
    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        # Verificar se o item já está no carrinho
        item_existente = CarrinhoItem.query.filter_by(
            usuario_id=usuario_id, 
            produto_id=produto_id
        ).first()
        
        if item_existente:
            # Atualizar quantidade
            item_existente.quantidade += 1
        else:
            # Criar novo item
            novo_item = CarrinhoItem(
                usuario_id=usuario_id,
                produto_id=produto_id,
                quantidade=1
            )
            db.session.add(novo_item)
        
        db.session.commit()
        registrar_log("INFO", f"Produto adicionado ao carrinho: ID {produto_id}", usuario_id)
    else:
        # Manter o comportamento da sessão para usuários não logados
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
    
    usuario_id = session['usuario_id']
    # Verificar se o bolo já está no carrinho
    item_existente = CarrinhoBoloPersonalizado.query.filter_by(
        usuario_id=usuario_id, 
        bolo_personalizado_id=bolo_id
    ).first()
    
    if item_existente:
        # Atualizar quantidade
        item_existente.quantidade += 1
    else:
        # Criar novo item
        novo_item = CarrinhoBoloPersonalizado(
            usuario_id=usuario_id,
            bolo_personalizado_id=bolo_id,
            quantidade=1
        )
        db.session.add(novo_item)
    
    db.session.commit()
    registrar_log("INFO", f"Bolo personalizado adicionado ao carrinho: ID {bolo_id}", usuario_id)
    
    flash(f'Bolo personalizado adicionado ao carrinho!', 'success')
    return redirect(url_for('cart.carrinho'))

@cart_bp.route('/remover_do_carrinho/<int:produto_id>')
def remover_do_carrinho(produto_id):
    if 'usuario_id' in session:
        # Remover do banco de dados
        item_existente = CarrinhoItem.query.filter_by(
            usuario_id=session['usuario_id'],
            produto_id=produto_id
        ).first()
        
        if item_existente:
            db.session.delete(item_existente)
            db.session.commit()
            registrar_log("INFO", f"Produto removido do carrinho: ID {produto_id}", session['usuario_id'])
            flash('Item removido do carrinho!', 'success')
        else:
            flash('Este item não está no seu carrinho', 'warning')
    else:
        # Remover da sessão
        if 'carrinho' in session:
            produto_id_str = str(produto_id)
            if produto_id_str in session['carrinho']:
                del session['carrinho'][produto_id_str]
                session.modified = True
                flash('Item removido do carrinho!', 'success')
            else:
                flash('Este item não está no seu carrinho', 'warning')
        else:
            flash('Seu carrinho está vazio', 'warning')
    
    return redirect(url_for('cart.carrinho'))

@cart_bp.route('/remover_bolo_personalizado/<int:bolo_id>')
def remover_bolo_personalizado(bolo_id):
    if 'usuario_id' in session:
        # Remover do banco de dados
        item_existente = CarrinhoBoloPersonalizado.query.filter_by(
            usuario_id=session['usuario_id'],
            bolo_personalizado_id=bolo_id
        ).first()
        
        if item_existente:
            db.session.delete(item_existente)
            db.session.commit()
            registrar_log("INFO", f"Bolo personalizado removido do carrinho: ID {bolo_id}", session['usuario_id'])
            flash('Bolo personalizado removido do carrinho!', 'success')
        else:
            flash('Este bolo não está no seu carrinho', 'warning')
    else:
        # Remover da sessão
        if 'carrinho_personalizado' in session:
            bolo_id_str = str(bolo_id)
            if bolo_id_str in session['carrinho_personalizado']:
                del session['carrinho_personalizado'][bolo_id_str]
                session.modified = True
                flash('Bolo personalizado removido do carrinho!', 'success')
            else:
                flash('Este bolo não está no seu carrinho', 'warning')
        else:
            flash('Seu carrinho de bolos personalizados está vazio', 'warning')
    
    return redirect(url_for('cart.carrinho'))

@cart_bp.route('/atualizar_carrinho', methods=['POST'])
def atualizar_carrinho():
    # Verificar se é uma requisição AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Atualizar carrinhos no banco de dados para usuários logados
    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        
        # Atualizar produtos regulares
        for produto_id, quantidade in request.form.items():
            if produto_id.startswith('quantidade_regular_'):
                produto_id_real = int(produto_id.replace('quantidade_regular_', ''))
                try:
                    nova_quantidade = int(quantidade)
                    if nova_quantidade > 0:
                        item = CarrinhoItem.query.filter_by(
                            usuario_id=usuario_id,
                            produto_id=produto_id_real
                        ).first()
                        if item:
                            item.quantidade = nova_quantidade
                except ValueError:
                    pass
        
        # Atualizar bolos personalizados
        for bolo_id, quantidade in request.form.items():
            if bolo_id.startswith('quantidade_personalizado_'):
                bolo_id_real = int(bolo_id.replace('quantidade_personalizado_', ''))
                try:
                    nova_quantidade = int(quantidade)
                    if nova_quantidade > 0:
                        item = CarrinhoBoloPersonalizado.query.filter_by(
                            usuario_id=usuario_id,
                            bolo_personalizado_id=bolo_id_real
                        ).first()
                        if item:
                            item.quantidade = nova_quantidade
                except ValueError:
                    pass
        
        db.session.commit()
        registrar_log("INFO", f"Carrinho atualizado", usuario_id)
    else:
        # Manter o comportamento da sessão para usuários não logados
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
    
    # Se for AJAX, retornar JSON sem redirect
    if is_ajax:
        return jsonify({
            'status': 'success',
            'message': 'Carrinho atualizado'
        })
    
    # Comportamento padrão (com redirect e sem mensagem)
    return redirect(url_for('cart.carrinho'))

# Quando um usuário faz login, transferir o carrinho da sessão para o banco de dados
@cart_bp.route('/sincronizar_carrinho')
def sincronizar_carrinho():
    if 'usuario_id' not in session:
        return jsonify({'status': 'error', 'message': 'Usuário não logado'})
    
    usuario_id = session['usuario_id']
    
    # Transferir produtos regulares
    if 'carrinho' in session and session['carrinho']:
        for item_id, item in session['carrinho'].items():
            produto_id = item['id']
            quantidade = item['quantidade']
            
            # Verificar se o item já existe no banco
            item_existente = CarrinhoItem.query.filter_by(
                usuario_id=usuario_id, 
                produto_id=produto_id
            ).first()
            
            if item_existente:
                # Somar as quantidades
                item_existente.quantidade += quantidade
            else:
                # Criar novo item
                novo_item = CarrinhoItem(
                    usuario_id=usuario_id,
                    produto_id=produto_id,
                    quantidade=quantidade
                )
                db.session.add(novo_item)
        
        # Limpar carrinho da sessão
        session.pop('carrinho')
    
    # Transferir bolos personalizados
    if 'carrinho_personalizado' in session and session['carrinho_personalizado']:
        for item_id, item in session['carrinho_personalizado'].items():
            bolo_id = item['id']
            quantidade = item['quantidade']
            
            # Verificar se o item já existe no banco
            item_existente = CarrinhoBoloPersonalizado.query.filter_by(
                usuario_id=usuario_id, 
                bolo_personalizado_id=bolo_id
            ).first()
            
            if item_existente:
                # Somar as quantidades
                item_existente.quantidade += quantidade
            else:
                # Criar novo item
                novo_item = CarrinhoBoloPersonalizado(
                    usuario_id=usuario_id,
                    bolo_personalizado_id=bolo_id,
                    quantidade=quantidade
                )
                db.session.add(novo_item)
        
        # Limpar carrinho personalizado da sessão
        session.pop('carrinho_personalizado')
    
    db.session.commit()
    registrar_log("INFO", f"Carrinho sincronizado", usuario_id)
    
    return jsonify({'status': 'success', 'message': 'Carrinho sincronizado com sucesso'})