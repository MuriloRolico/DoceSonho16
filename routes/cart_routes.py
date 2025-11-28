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

def calcular_totais_carrinho(usuario_id=None):
    """
    Calcula os totais do carrinho e valida preços e quantidades
    Retorna: (itens_regulares, itens_personalizados, total, erros)
    """
    itens_regulares = []
    itens_personalizados = []
    total = 0
    erros = []
    
    if usuario_id:
        # Buscar itens regulares do banco de dados
        itens_db = CarrinhoItem.query.filter_by(usuario_id=usuario_id).all()
        for item in itens_db:
            produto = Produto.query.get(item.produto_id)
            if produto and produto.ativo:
                # Validar quantidade
                if item.quantidade <= 0:
                    erros.append(f"Quantidade inválida para {produto.nome}")
                    continue
                if item.quantidade > 10:
                    item.quantidade = 10
                    db.session.commit()
                    erros.append(f"Quantidade de {produto.nome} ajustada para o máximo permitido (10)")
                
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
            else:
                # Produto não existe ou está inativo, remover do carrinho
                db.session.delete(item)
                db.session.commit()
                erros.append(f"Produto ID {item.produto_id} removido do carrinho (não disponível)")
        
        # Buscar bolos personalizados do banco de dados
        bolos_db = CarrinhoBoloPersonalizado.query.filter_by(usuario_id=usuario_id).all()
        for item in bolos_db:
            bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
            if bolo:
                # Validar quantidade
                if item.quantidade <= 0:
                    erros.append(f"Quantidade inválida para bolo personalizado")
                    continue
                if item.quantidade > 10:
                    item.quantidade = 10
                    db.session.commit()
                    erros.append(f"Quantidade de bolo personalizado ajustada para o máximo permitido (10)")
                
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
                # Bolo não existe, remover do carrinho
                db.session.delete(item)
                db.session.commit()
                erros.append(f"Bolo personalizado ID {item.bolo_personalizado_id} removido do carrinho (não disponível)")
    else:
        # Carrinho na sessão para usuários não logados
        if 'carrinho' in session and session['carrinho']:
            carrinho_atualizado = {}
            for item_id, item in session['carrinho'].items():
                produto = Produto.query.filter_by(id=item['id'], ativo=True).first()
                if produto:
                    # Validar e ajustar quantidade
                    quantidade = item['quantidade']
                    if quantidade <= 0:
                        continue
                    if quantidade > 10:
                        quantidade = 10
                        erros.append(f"Quantidade de {produto.nome} ajustada para o máximo permitido (10)")
                    
                    # Validar preço
                    if item['preco'] != produto.preco:
                        erros.append(f"Preço de {produto.nome} atualizado")
                    
                    subtotal = produto.preco * quantidade
                    total += subtotal
                    
                    carrinho_atualizado[item_id] = {
                        'id': produto.id,
                        'nome': produto.nome,
                        'preco': produto.preco,
                        'quantidade': quantidade
                    }
                    
                    itens_regulares.append({
                        'id': produto.id,
                        'nome': produto.nome,
                        'preco': produto.preco,
                        'quantidade': quantidade,
                        'subtotal': subtotal,
                        'tipo': 'regular'
                    })
                else:
                    erros.append(f"Produto removido do carrinho (não disponível)")
            
            session['carrinho'] = carrinho_atualizado
        
        if 'carrinho_personalizado' in session and session['carrinho_personalizado']:
            carrinho_personalizado_atualizado = {}
            for item_id, item in session['carrinho_personalizado'].items():
                bolo = BoloPersonalizado.query.get(item['id'])
                if bolo:
                    # Validar e ajustar quantidade
                    quantidade = item['quantidade']
                    if quantidade <= 0:
                        continue
                    if quantidade > 10:
                        quantidade = 10
                        erros.append(f"Quantidade de bolo personalizado ajustada para o máximo permitido (10)")
                    
                    # Validar preço
                    if item['preco'] != bolo.preco:
                        erros.append(f"Preço de bolo personalizado atualizado")
                    
                    subtotal = bolo.preco * quantidade
                    total += subtotal
                    
                    carrinho_personalizado_atualizado[item_id] = {
                        'id': bolo.id,
                        'nome': item['nome'],
                        'massa': item.get('massa', ''),
                        'recheios': item.get('recheios', ''),
                        'cobertura': item.get('cobertura', ''),
                        'finalizacao': item.get('finalizacao', ''),
                        'observacoes': item.get('observacoes', ''),
                        'preco': bolo.preco,
                        'quantidade': quantidade
                    }
                    
                    itens_personalizados.append({
                        'id': bolo.id,
                        'nome': item['nome'],
                        'massa': formatar_campo_simples(item.get('massa', '')),
                        'recheios': formatar_lista_json(item.get('recheios', '')),
                        'cobertura': formatar_campo_simples(item.get('cobertura', '')),
                        'finalizacao': formatar_lista_json(item.get('finalizacao', '')),
                        'observacoes': item.get('observacoes', ''),
                        'preco': bolo.preco,
                        'quantidade': quantidade,
                        'subtotal': subtotal,
                        'tipo': 'personalizado'
                    })
                else:
                    erros.append(f"Bolo personalizado removido do carrinho (não disponível)")
            
            session['carrinho_personalizado'] = carrinho_personalizado_atualizado
    
    return itens_regulares, itens_personalizados, total, erros

@cart_bp.route('/carrinho')
def carrinho():
    usuario_id = session.get('usuario_id')
    
    # Calcular totais e validar carrinho
    itens_regulares, itens_personalizados, total, erros = calcular_totais_carrinho(usuario_id)
    
    # Mostrar erros se houver
    for erro in erros:
        flash(erro, 'warning')
    
    # Combinar os dois tipos de itens
    todos_itens = itens_regulares + itens_personalizados
    
    return render_template('carrinho.html', itens=todos_itens, total=total)

@cart_bp.route('/adicionar/<int:produto_id>')
def adicionar_ao_carrinho(produto_id):
    # Verificar se produto existe e está ativo
    produto = Produto.query.filter_by(id=produto_id, ativo=True).first_or_404()
    
    # Se o usuário estiver logado, salvar no banco de dados
    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        # Verificar se o item já está no carrinho
        item_existente = CarrinhoItem.query.filter_by(
            usuario_id=usuario_id, 
            produto_id=produto_id
        ).first()
        
        if item_existente:
            # Verificar limite de quantidade
            if item_existente.quantidade >= 10:
                flash(f'Quantidade máxima de {produto.nome} atingida (10 unidades)', 'warning')
            else:
                item_existente.quantidade += 1
                db.session.commit()
                flash(f'{produto.nome} adicionado ao carrinho!', 'success')
        else:
            # Criar novo item
            novo_item = CarrinhoItem(
                usuario_id=usuario_id,
                produto_id=produto_id,
                quantidade=1
            )
            db.session.add(novo_item)
            db.session.commit()
            flash(f'{produto.nome} adicionado ao carrinho!', 'success')
        
        registrar_log("INFO", f"Produto adicionado ao carrinho: ID {produto_id}", usuario_id)
    else:
        # Manter o comportamento da sessão para usuários não logados
        if 'carrinho' not in session:
            session['carrinho'] = {}
        
        carrinho = session['carrinho']
        produto_id_str = str(produto_id)
        
        if produto_id_str in carrinho:
            if carrinho[produto_id_str]['quantidade'] >= 10:
                flash(f'Quantidade máxima de {produto.nome} atingida (10 unidades)', 'warning')
            else:
                carrinho[produto_id_str]['quantidade'] += 1
                flash(f'{produto.nome} adicionado ao carrinho!', 'success')
        else:
            carrinho[produto_id_str] = {
                'id': produto_id,
                'nome': produto.nome,
                'preco': produto.preco,
                'quantidade': 1
            }
            flash(f'{produto.nome} adicionado ao carrinho!', 'success')
        
        session['carrinho'] = carrinho
    
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
        # Verificar limite de quantidade
        if item_existente.quantidade >= 10:
            flash(f'Quantidade máxima de bolo personalizado atingida (10 unidades)', 'warning')
        else:
            item_existente.quantidade += 1
            db.session.commit()
            flash(f'Bolo personalizado adicionado ao carrinho!', 'success')
    else:
        # Criar novo item
        novo_item = CarrinhoBoloPersonalizado(
            usuario_id=usuario_id,
            bolo_personalizado_id=bolo_id,
            quantidade=1
        )
        db.session.add(novo_item)
        db.session.commit()
        flash(f'Bolo personalizado adicionado ao carrinho!', 'success')
    
    registrar_log("INFO", f"Bolo personalizado adicionado ao carrinho: ID {bolo_id}", usuario_id)
    
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

@cart_bp.route('/atualizar_quantidade', methods=['POST'])
def atualizar_quantidade():
    """
    Endpoint para atualização automática de quantidade via AJAX
    """
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        item_tipo = data.get('item_tipo')
        nova_quantidade = int(data.get('quantidade'))
        
        # Validar quantidade
        if nova_quantidade < 1:
            return jsonify({
                'status': 'error',
                'message': 'Quantidade mínima é 1'
            }), 400
        
        if nova_quantidade > 10:
            return jsonify({
                'status': 'error',
                'message': 'Quantidade máxima é 10'
            }), 400
        
        if 'usuario_id' in session:
            usuario_id = session['usuario_id']
            
            if item_tipo == 'regular':
                item = CarrinhoItem.query.filter_by(
                    usuario_id=usuario_id,
                    produto_id=item_id
                ).first()
                
                if item:
                    item.quantidade = nova_quantidade
                    db.session.commit()
                    
                    # Calcular novo subtotal
                    produto = Produto.query.get(item_id)
                    subtotal = produto.preco * nova_quantidade
                    
                    # Recalcular total do carrinho
                    _, _, total, _ = calcular_totais_carrinho(usuario_id)
                    
                    return jsonify({
                        'status': 'success',
                        'subtotal': subtotal,
                        'total': total
                    })
            else:  # personalizado
                item = CarrinhoBoloPersonalizado.query.filter_by(
                    usuario_id=usuario_id,
                    bolo_personalizado_id=item_id
                ).first()
                
                if item:
                    item.quantidade = nova_quantidade
                    db.session.commit()
                    
                    # Calcular novo subtotal
                    bolo = BoloPersonalizado.query.get(item_id)
                    subtotal = bolo.preco * nova_quantidade
                    
                    # Recalcular total do carrinho
                    _, _, total, _ = calcular_totais_carrinho(usuario_id)
                    
                    return jsonify({
                        'status': 'success',
                        'subtotal': subtotal,
                        'total': total
                    })
        else:
            # Atualizar sessão
            if item_tipo == 'regular' and 'carrinho' in session:
                item_id_str = str(item_id)
                if item_id_str in session['carrinho']:
                    session['carrinho'][item_id_str]['quantidade'] = nova_quantidade
                    session.modified = True
                    
                    # Calcular novo subtotal
                    produto = Produto.query.get(item_id)
                    subtotal = produto.preco * nova_quantidade
                    
                    # Recalcular total
                    _, _, total, _ = calcular_totais_carrinho()
                    
                    return jsonify({
                        'status': 'success',
                        'subtotal': subtotal,
                        'total': total
                    })
            elif item_tipo == 'personalizado' and 'carrinho_personalizado' in session:
                item_id_str = str(item_id)
                if item_id_str in session['carrinho_personalizado']:
                    session['carrinho_personalizado'][item_id_str]['quantidade'] = nova_quantidade
                    session.modified = True
                    
                    # Calcular novo subtotal
                    bolo = BoloPersonalizado.query.get(item_id)
                    subtotal = bolo.preco * nova_quantidade
                    
                    # Recalcular total
                    _, _, total, _ = calcular_totais_carrinho()
                    
                    return jsonify({
                        'status': 'success',
                        'subtotal': subtotal,
                        'total': total
                    })
        
        return jsonify({
            'status': 'error',
            'message': 'Item não encontrado'
        }), 404
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cart_bp.route('/validar_carrinho', methods=['GET'])
def validar_carrinho():
    """
    Endpoint para validação completa do carrinho
    """
    usuario_id = session.get('usuario_id')
    _, _, total, erros = calcular_totais_carrinho(usuario_id)
    
    return jsonify({
        'status': 'success',
        'total': total,
        'erros': erros,
        'valido': len(erros) == 0
    })

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
                # Somar as quantidades (respeitando o limite)
                nova_quantidade = min(item_existente.quantidade + quantidade, 10)
                item_existente.quantidade = nova_quantidade
            else:
                # Criar novo item
                novo_item = CarrinhoItem(
                    usuario_id=usuario_id,
                    produto_id=produto_id,
                    quantidade=min(quantidade, 10)
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
                # Somar as quantidades (respeitando o limite)
                nova_quantidade = min(item_existente.quantidade + quantidade, 10)
                item_existente.quantidade = nova_quantidade
            else:
                # Criar novo item
                novo_item = CarrinhoBoloPersonalizado(
                    usuario_id=usuario_id,
                    bolo_personalizado_id=bolo_id,
                    quantidade=min(quantidade, 10)
                )
                db.session.add(novo_item)
        
        # Limpar carrinho personalizado da sessão
        session.pop('carrinho_personalizado')
    
    db.session.commit()
    registrar_log("INFO", f"Carrinho sincronizado", usuario_id)
    
    return jsonify({'status': 'success', 'message': 'Carrinho sincronizado com sucesso'})