from flask import Blueprint, render_template, request, redirect, url_for, flash, session , current_app
from database import db
from models.models import Produto, BoloPersonalizado
import json
from werkzeug.utils import secure_filename
import os
from utils.helpers import is_admin, allowed_file, registrar_log


product_bp = Blueprint('product', __name__)

@product_bp.route('/produtos')
def todos_produtos():
    produtos = Produto.query.all()
    # Buscando todas as categorias distintas do banco de dados
    categorias = db.session.query(Produto.categoria).distinct().all()
    # Convertendo para lista simples e removendo valores vazios
    categorias = [categoria[0] for categoria in categorias if categoria[0]]
    return render_template('todos_produtos.html', produtos=produtos, categorias=categorias)

@product_bp.route('/produto/<int:produto_id>')
def detalhes_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    return render_template('detalhes_produto.html', produto=produto)

@product_bp.route('/montar-bolo')
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
        massa=massa,
        recheios=recheios_json,
        cobertura=cobertura,
        finalizacao=finalizacao_json,
        observacoes=observacoes,
        preco=preco_total
    )
    
    db.session.add(novo_bolo)
    db.session.commit()
    
    # Adicionar ao carrinho automaticamente
    if 'carrinho_personalizado' not in session:
        session['carrinho_personalizado'] = {}
    
    bolo_id_str = str(novo_bolo.id)
    
    carrinho_personalizado = session['carrinho_personalizado']
    carrinho_personalizado[bolo_id_str] = {
        'id': novo_bolo.id,
        'nome': f"Bolo Personalizado de {novo_bolo.massa.capitalize()}",
        'preco': novo_bolo.preco,
        'quantidade': 1
    }
    
    session['carrinho_personalizado'] = carrinho_personalizado
    
    flash(f'Seu bolo personalizado foi criado e adicionado ao carrinho!', 'success')
    return redirect(url_for('cart.carrinho'))

@product_bp.route('/meus-bolos')
def meus_bolos():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para ver seus bolos personalizados', 'warning')
        return redirect(url_for('auth.login'))
    
    bolos = BoloPersonalizado.query.filter_by(usuario_id=session['usuario_id'], ativo=True).all()
    return render_template('meus_bolos.html', bolos=bolos)

@product_bp.route('/bolo-personalizado/<int:bolo_id>')
def detalhes_bolo_personalizado(bolo_id):
    if 'usuario_id' not in session:
        flash('Faça login para visualizar detalhes do bolo personalizado', 'warning')
        return redirect(url_for('auth.login'))
    
    bolo = BoloPersonalizado.query.get_or_404(bolo_id)
    
    # Verificar se o bolo pertence ao usuário
    if bolo.usuario_id != session['usuario_id'] and not is_admin():
        flash('Você não tem permissão para visualizar este bolo', 'danger')
        return redirect(url_for('index'))
    
    # Converter os campos JSON para listas
    recheios = json.loads(bolo.recheios)
    finalizacao = json.loads(bolo.finalizacao) if bolo.finalizacao else []
    
    return render_template('detalhes_bolo_personalizado.html', bolo=bolo, recheios=recheios, finalizacao=finalizacao)

