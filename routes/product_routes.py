from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from database import db
from models.models import Produto, BoloPersonalizado, CarrinhoBoloPersonalizado, Usuario
from utils.helpers import is_admin, allowed_file, registrar_log
import os
from werkzeug.utils import secure_filename
from sqlalchemy import desc
import json
from utils.helpers import funcionario_bloqueado

product_bp = Blueprint('product', __name__)

# No arquivo product_bp.py (ou onde estiver a rota 'todos_produtos')

@product_bp.route('/produtos')
@funcionario_bloqueado
def todos_produtos():
    # Modificar a consulta para buscar apenas produtos ativos
    produtos = Produto.query.filter_by(ativo=True).all()
    # Buscando todas as categorias distintas de produtos ativos
    categorias = db.session.query(Produto.categoria).filter_by(ativo=True).distinct().all()
    # Convertendo para lista simples e removendo valores vazios
    categorias = [categoria[0] for categoria in categorias if categoria[0]]
    return render_template('todos_produtos.html', produtos=produtos, categorias=categorias)

@product_bp.route('/produto/<int:produto_id>')
@funcionario_bloqueado
def detalhes_produto(produto_id):
    # Buscar produto e verificar se está ativo
    produto = Produto.query.filter_by(id=produto_id, ativo=True).first_or_404()
    return render_template('detalhes_produto.html', produto=produto)



@product_bp.route('/montar-bolo')
@funcionario_bloqueado
def montar_bolo():
    # Verificar se o usuário está logado
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para montar seu bolo personalizado', 'warning')
        return redirect(url_for('auth.login'))
    
    return render_template('montar_bolo.html')

@product_bp.route('/montar-bolo/salvar', methods=['POST'])
def salvar_bolo_personalizado():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para salvar seu bolo personalizado', 'warning')
        return redirect(url_for('auth.login'))
    
    # Obter os dados do formulário
    massa = request.form.get('massa')
    recheios = request.form.getlist('recheios')
    cobertura = request.form.get('cobertura')
    finalizacao = request.form.getlist('finalizacao')
    observacoes = request.form.get('observacoes')
    
    # Verificar se os campos obrigatórios foram preenchidos
    if not massa or not recheios or not cobertura:
        flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('product.montar_bolo'))
    
    # Calcular o preço com base nas escolhas
    preco_base = 50.00  # Preço base do bolo
    
    # Preços por tipo de item
    precos = {
        'massa': {
            'chocolate': 25.00,
            'baunilha': 20.00,
            'red_velvet': 30.00,
            'limao': 22.00
        },
        'recheio': {
            'brigadeiro': 15.00,
            'morango': 18.00,
            'doce_de_leite': 12.00,
            'chocolate_branco': 16.00
        },
        'cobertura': {
            'chantilly': 18.00,
            'ganache': 20.00,
            'pasta_americana': 25.00,
            'cream_cheese': 22.00
        },
        'finalizacao': {
            'morangos': 12.00,
            'chocolate_raspas': 8.00,
            'mm': 10.00,
            'confete': 5.00
        }
    }
    
    # Calcular o preço total
    preco_total = preco_base
    
    # Adicionar preço da massa
    if massa in precos['massa']:
        preco_total += precos['massa'][massa]
    
    # Adicionar preço dos recheios
    for recheio in recheios:
        if recheio in precos['recheio']:
            preco_total += precos['recheio'][recheio]
    
    # Adicionar preço da cobertura
    if cobertura in precos['cobertura']:
        preco_total += precos['cobertura'][cobertura]
    
    # Adicionar preço das finalizações
    for item in finalizacao:
        if item in precos['finalizacao']:
            preco_total += precos['finalizacao'][item]
    
    # Converter listas para JSON
    recheios_json = json.dumps(recheios)
    finalizacao_json = json.dumps(finalizacao)
    
    # Criar um novo bolo personalizado
    novo_bolo = BoloPersonalizado(
        usuario_id=session['usuario_id'],
        nome=f"Bolo Personalizado de {massa.capitalize()}",  # Adicionando nome mais descritivo
        massa=massa,
        recheios=recheios_json,
        cobertura=cobertura,
        finalizacao=finalizacao_json,
        observacoes=observacoes,
        preco=preco_total
    )
    
    try:
        db.session.add(novo_bolo)
        db.session.commit()
        
        # Registrar log
        registrar_log("INFO", f"Bolo personalizado criado: ID {novo_bolo.id}", session['usuario_id'])
        
        # Adicionar ao carrinho automaticamente
        novo_item_carrinho = CarrinhoBoloPersonalizado(
            usuario_id=session['usuario_id'],
            bolo_personalizado_id=novo_bolo.id,
            quantidade=1
        )
        db.session.add(novo_item_carrinho)
        db.session.commit()
        
        registrar_log("INFO", f"Bolo personalizado adicionado ao carrinho: ID {novo_bolo.id}", session['usuario_id'])
        
        flash('Seu bolo personalizado foi criado e adicionado ao carrinho!', 'success')
        return redirect(url_for('cart.carrinho'))
    except Exception as e:
        db.session.rollback()
        registrar_log("ERROR", f"Erro ao criar bolo personalizado: {str(e)}", session.get('usuario_id'))
        flash(f'Erro ao salvar o bolo personalizado: {str(e)}', 'danger')
        return redirect(url_for('product.montar_bolo'))

# Rota para a página "Meus Bolos"
@product_bp.route('/meus-bolos')
def meus_bolos():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para ver seus bolos personalizados', 'warning')
        return redirect(url_for('auth.login'))
    
    # Buscar os bolos personalizados do usuário atual
    bolos = BoloPersonalizado.query.filter_by(usuario_id=session['usuario_id']).order_by(
        desc(BoloPersonalizado.data_criacao)).all()
    
    return render_template('meus_bolos.html', bolos=bolos)

# Rota para a página "Detalhes do Bolo Personalizado"
@product_bp.route('/bolo-personalizado/<int:bolo_id>')
def detalhes_bolo_personalizado(bolo_id):
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para ver detalhes de bolos personalizados', 'warning')
        return redirect(url_for('auth.login'))
    
    # Buscar o bolo pelo ID
    bolo = BoloPersonalizado.query.get_or_404(bolo_id)
    
    # Verificar se o bolo pertence ao usuário atual
    if bolo.usuario_id != session['usuario_id']:
        flash('Você não tem permissão para ver este bolo', 'danger')
        return redirect(url_for('product.meus_bolos'))
    
    # Converter os campos JSON para listas
    recheios = json.loads(bolo.recheios) if bolo.recheios else []
    finalizacao = json.loads(bolo.finalizacao) if bolo.finalizacao else []
    
    return render_template('detalhes_bolo_personalizado.html', bolo=bolo, recheios=recheios, finalizacao=finalizacao)

# Rota para adicionar bolo personalizado ao carrinho
@product_bp.route('/bolo-personalizado/<int:bolo_id>/adicionar-ao-carrinho')
def adicionar_bolo_personalizado_ao_carrinho(bolo_id):
    # Redirecionamento para a rota existente no cart_bp
    return redirect(url_for('cart.adicionar_bolo_personalizado_ao_carrinho', bolo_id=bolo_id))