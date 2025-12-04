from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from database import db
from models.models import Produto, Log, Pedido, ItemPedido, ItemPedidoPersonalizado, BoloPersonalizado, Usuario
from datetime import datetime, timedelta, date
from functools import wraps
from werkzeug.utils import secure_filename
import os
from utils.helpers import registrar_log, allowed_file

funcionario_bp = Blueprint('funcionario', __name__)

# Decorator para verificar se é funcionário
def funcionario_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa fazer login para acessar esta área.', 'danger')
            return redirect(url_for('auth.login'))
        
        usuario = Usuario.query.get(session['usuario_id'])
        
        if not usuario:
            flash('Usuário não encontrado.', 'danger')
            session.clear()
            return redirect(url_for('auth.login'))
        
        if not usuario.is_funcionario:
            flash('Acesso negado. Apenas funcionários podem acessar esta área.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Dashboard do funcionário
@funcionario_bp.route('/funcionario')
@funcionario_required
def dashboard():
    # Estatísticas básicas para o funcionário
    total_pedidos_pendentes = Pedido.query.filter_by(status='Pendente').count()
    total_pedidos_hoje = Pedido.query.filter(
        db.func.date(Pedido.data) == datetime.utcnow().date()
    ).count()
    
    # Pedidos recentes
    pedidos_recentes = Pedido.query.order_by(Pedido.data.desc()).limit(10).all()
    
    return render_template('funcionario/dashboard.html',
                         total_pedidos_pendentes=total_pedidos_pendentes,
                         total_pedidos_hoje=total_pedidos_hoje,
                         pedidos_recentes=pedidos_recentes)

# ==================== ROTAS DE PEDIDOS ====================

@funcionario_bp.route('/funcionario/pedidos')
@funcionario_required
def pedidos():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    status = request.args.get('status', '')
    
    query = Pedido.query
    
    if status:
        query = query.filter(Pedido.status == status)
    
    pedidos = query.order_by(Pedido.data.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('funcionario/pedidos.html', pedidos=pedidos, status_atual=status)

@funcionario_bp.route('/funcionario/pedido/<int:pedido_id>')
@funcionario_required
def detalhes_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    usuario = Usuario.query.get(pedido.usuario_id)
    
    # Obter itens regulares
    itens_regulares = ItemPedido.query.filter_by(pedido_id=pedido.id).all()
    
    detalhes_itens_regulares = []
    for item in itens_regulares:
        produto = Produto.query.get(item.produto_id)
        
        if produto:
            nome_produto = produto.nome
            if not produto.ativo:
                nome_produto += " (Produto descontinuado)"
        else:
            nome_produto = "Produto removido"
        
        detalhes_itens_regulares.append({
            'nome': nome_produto,
            'quantidade': item.quantidade,
            'preco_unitario': item.preco_unitario,
            'subtotal': item.preco_unitario * item.quantidade,
            'tipo': 'regular',
            'produto_ativo': produto.ativo if produto else False,
            'produto': produto
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
            'bolo_id': bolo.id,
            'bolo': bolo
        })
    
    # Combinar os dois tipos de itens
    todos_itens = detalhes_itens_regulares + detalhes_itens_personalizados
    
    # Obtém histórico de atualizações de status
    historico_status = Log.query.filter(
        Log.tipo == 'pedido_atualizado',
        Log.descricao.like(f'Pedido #{pedido.id} atualizado%')
    ).order_by(Log.data.desc()).all()
    
    return render_template('funcionario/detalhes_pedido.html', 
                          pedido=pedido, 
                          itens=todos_itens, 
                          usuario=usuario,
                          historico_status=historico_status)

@funcionario_bp.route('/funcionario/pedido/<int:pedido_id>/atualizar', methods=['GET', 'POST'])
@funcionario_required
def atualizar_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    usuario = Usuario.query.get(pedido.usuario_id)
    
    # PROTEÇÃO: Verificar se o pedido está cancelado
    if pedido.status == 'Cancelado':
        flash('Este pedido está cancelado e não pode mais ser alterado. Esta é uma ação irreversível.', 'danger')
        return redirect(url_for('funcionario.detalhes_pedido', pedido_id=pedido.id))
    
    if request.method == 'POST':
        status_anterior = pedido.status
        novo_status = request.form.get('status')
        observacoes = request.form.get('observacoes', '')
        
        if novo_status and novo_status != status_anterior:
            pedido.status = novo_status
            
            # Adicionar observações ao pedido
            if observacoes:
                if pedido.observacoes_admin:
                    pedido.observacoes_admin += f"\n\n[{datetime.now().strftime('%d/%m/%Y %H:%M')}] {observacoes}"
                else:
                    pedido.observacoes_admin = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] {observacoes}"
            
            db.session.commit()
            
            # Registrar o log de atualização
            descricao = f'Pedido #{pedido.id} atualizado de "{status_anterior}" para "{novo_status}" por funcionário'
            if observacoes:
                descricao += f' com observação: "{observacoes}"'
            
            # Se o pedido foi cancelado, adicionar aviso no log
            if novo_status == 'Cancelado':
                descricao += ' - AÇÃO IRREVERSÍVEL'
                
            registrar_log(
                tipo='pedido_atualizado',
                descricao=descricao,
                usuario_id=session.get('usuario_id')
            )
            
            # Mensagem especial se cancelado
            if novo_status == 'Cancelado':
                flash(f'Pedido #{pedido.id} foi CANCELADO. Esta é uma ação IRREVERSÍVEL e o pedido não poderá mais ser alterado.', 'warning')
            else:
                flash(f'Status do pedido atualizado para: {novo_status}', 'success')
            
            return redirect(url_for('funcionario.detalhes_pedido', pedido_id=pedido.id))
    
    # Obter histórico de status
    historico_status = Log.query.filter(
        Log.tipo == 'pedido_atualizado',
        Log.descricao.like(f'Pedido #{pedido.id} atualizado%')
    ).order_by(Log.data.desc()).all()
    
    # Obter itens do pedido
    itens_regulares = ItemPedido.query.filter_by(pedido_id=pedido.id).all()
    itens_personalizados = ItemPedidoPersonalizado.query.filter_by(pedido_id=pedido.id).all()
    
    # Processar itens regulares
    detalhes_itens_regulares = []
    for item in itens_regulares:
        produto = Produto.query.get(item.produto_id)
        if produto:
            nome_produto = produto.nome
            if not produto.ativo:
                nome_produto += " (Produto descontinuado)"
        else:
            nome_produto = "Produto removido"
        
        detalhes_itens_regulares.append({
            'nome': nome_produto,
            'quantidade': item.quantidade,
            'preco_unitario': item.preco_unitario,
            'subtotal': item.preco_unitario * item.quantidade,
            'tipo': 'regular'
        })
    
    # Processar itens personalizados
    detalhes_itens_personalizados = []
    for item in itens_personalizados:
        bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
        detalhes_itens_personalizados.append({
            'nome': f"Bolo Personalizado de {bolo.massa.capitalize()}",
            'quantidade': item.quantidade,
            'preco_unitario': item.preco_unitario,
            'subtotal': item.preco_unitario * item.quantidade,
            'tipo': 'personalizado',
            'bolo_id': bolo.id,
            'bolo': bolo
        })
    
    # Combinar os dois tipos de itens
    todos_itens = detalhes_itens_regulares + detalhes_itens_personalizados
    
    return render_template('funcionario/atualizar_pedido.html', 
                          pedido=pedido, 
                          itens=todos_itens,
                          usuario=usuario,
                          historico_status=historico_status)

# NOVA ROTA: Criar pedido manualmente (VERSÃO CORRIGIDA)
@funcionario_bp.route('/funcionario/pedidos/novo', methods=['GET', 'POST'])
@funcionario_required
def novo_pedido():
    if request.method == 'POST':
        try:
            # Dicionário com preços fixos dos bolos
            PRECOS_BOLOS_FIXOS = {
                '1': 119.00,   # Chocolate
                '2': 125.00,   # Morango
                '3': 135.00,   # Red Velvet
                '4': 127.90    # Limão
            }
            
            # Obter dados do formulário
            usuario_id = request.form.get('usuario_id')
            tipo_entrega = request.form.get('tipo_entrega')
            observacoes = request.form.get('observacoes', '')
            
            # Validar campos obrigatórios
            if not usuario_id:
                flash('Selecione um cliente para o pedido', 'danger')
                return redirect(url_for('funcionario.novo_pedido'))
            
            # Verificar se o usuário existe
            usuario = Usuario.query.get(usuario_id)
            if not usuario:
                flash('Cliente não encontrado', 'danger')
                return redirect(url_for('funcionario.novo_pedido'))
            
            # Calcular valor do frete
            valor_frete = 12.00 if tipo_entrega == 'frete' else 0.00
            
            # Obter itens do pedido
            produtos_ids = request.form.getlist('produto_id')
            bolos_ids = request.form.getlist('bolo_personalizado_id')
            quantidades = request.form.getlist('quantidade')
            
            if not produtos_ids and not bolos_ids:
                flash('Adicione pelo menos um item ao pedido', 'danger')
                return redirect(url_for('funcionario.novo_pedido'))
            
            # Calcular total
            total = valor_frete
            itens_validos = []
            bolos_validos = []
            
            # Processar produtos regulares e bolos
            for i, quantidade_str in enumerate(quantidades):
                if not quantidade_str:
                    continue
                    
                qtd = int(quantidade_str)
                if qtd <= 0:
                    continue
                
                # Verificar se é um produto regular
                if i < len(produtos_ids) and produtos_ids[i]:
                    produto = Produto.query.get(produtos_ids[i])
                    if produto and produto.ativo:
                        subtotal = produto.preco * qtd
                        total += subtotal
                        itens_validos.append({
                            'produto': produto,
                            'quantidade': qtd
                        })
                
                # Verificar se é um bolo personalizado
                elif i < len(bolos_ids) and bolos_ids[i]:
                    bolo_id = bolos_ids[i]
                    if bolo_id in PRECOS_BOLOS_FIXOS:
                        preco_bolo = PRECOS_BOLOS_FIXOS[bolo_id]
                        subtotal = preco_bolo * qtd
                        total += subtotal
                        bolos_validos.append({
                            'bolo_id': bolo_id,
                            'quantidade': qtd,
                            'preco': preco_bolo
                        })
            
            if not itens_validos and not bolos_validos:
                flash('Nenhum item válido foi adicionado ao pedido', 'danger')
                return redirect(url_for('funcionario.novo_pedido'))
            
            # ====================================================
            # CRIAR PEDIDO COM OS NOVOS CAMPOS
            # ====================================================
            novo_pedido = Pedido(
                usuario_id=usuario_id,
                status='Aprovado',
                tipo_entrega=tipo_entrega,
                valor_frete=valor_frete,
                observacoes=observacoes,
                total=total,
                criado_manualmente=True,  # NOVO CAMPO
                criado_por_funcionario_id=session.get('usuario_id')  # NOVO CAMPO
            )
            
            db.session.add(novo_pedido)
            db.session.flush()  # Garantir que o ID seja gerado
            
            current_app.logger.info(f"Pedido criado: ID={novo_pedido.id}, Usuario={usuario_id}, Total={total}")
            
            # Adicionar produtos regulares ao pedido
            for item in itens_validos:
                item_pedido = ItemPedido(
                    pedido_id=novo_pedido.id,
                    produto_id=item['produto'].id,
                    quantidade=item['quantidade'],
                    preco_unitario=item['produto'].preco
                )
                db.session.add(item_pedido)
                current_app.logger.info(f"Item adicionado: Produto={item['produto'].id}, Qtd={item['quantidade']}")
            
            # Adicionar bolos personalizados ao pedido
            SABORES_BOLOS = {
                '1': 'chocolate',
                '2': 'morango',
                '3': 'red velvet',
                '4': 'limão'
            }
            
            for item in bolos_validos:
                # Criar o bolo personalizado no banco
                sabor = SABORES_BOLOS.get(item['bolo_id'], 'chocolate')
                novo_bolo = BoloPersonalizado(
                    usuario_id=usuario_id,
                    nome=f"Bolo Personalizado de {sabor.capitalize()}",
                    massa=sabor,
                    recheios=f"Recheio de {sabor}",
                    cobertura=f"Cobertura de {sabor}",
                    finalizacao="Finalização padrão",
                    observacoes="Criado manualmente pelo funcionário",
                    preco=item['preco'],
                    ativo=True
                )
                db.session.add(novo_bolo)
                db.session.flush()  # Gerar o ID do bolo
                
                current_app.logger.info(f"Bolo criado: ID={novo_bolo.id}, Sabor={sabor}")
                
                # Adicionar ao pedido
                item_pedido = ItemPedidoPersonalizado(
                    pedido_id=novo_pedido.id,
                    bolo_personalizado_id=novo_bolo.id,
                    quantidade=item['quantidade'],
                    preco_unitario=item['preco']
                )
                db.session.add(item_pedido)
                current_app.logger.info(f"Item bolo adicionado: Bolo={novo_bolo.id}, Qtd={item['quantidade']}")
            
            # COMMIT FINAL - MUITO IMPORTANTE!
            db.session.commit()
            current_app.logger.info(f"COMMIT REALIZADO! Pedido #{novo_pedido.id} salvo com sucesso")
            
            # Registrar log
            registrar_log(
                tipo='pedido_criado',
                descricao=f'Pedido #{novo_pedido.id} criado manualmente por funcionário para cliente {usuario.nome}',
                usuario_id=session.get('usuario_id')
            )
            
            flash(f'Pedido #{novo_pedido.id} criado com sucesso!', 'success')
            return redirect(url_for('funcionario.detalhes_pedido', pedido_id=novo_pedido.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'ERRO ao criar pedido: {str(e)}')
            current_app.logger.error('Traceback:', exc_info=True)
            flash(f'Erro ao criar pedido: {str(e)}', 'danger')
            return redirect(url_for('funcionario.novo_pedido'))
    
    # GET - Renderizar formulário
    clientes = Usuario.query.filter_by(is_admin=False, is_funcionario=False, status='ativo').order_by(Usuario.nome).all()
    produtos_ativos = Produto.ativos().all()
    
    return render_template('funcionario/novo_pedido.html', 
                          clientes=clientes, 
                          produtos=produtos_ativos)

# ==================== ROTAS DE PRODUTOS ====================

@funcionario_bp.route('/funcionario/produtos')
@funcionario_required
def produtos():
    # Agora com permissão de edição
    produtos_ativos = Produto.ativos().all()
    produtos_inativos = Produto.inativos().all()
    
    return render_template('funcionario/produtos.html', 
                         produtos_ativos=produtos_ativos,
                         produtos_inativos=produtos_inativos)

@funcionario_bp.route('/funcionario/produto/<int:produto_id>')
@funcionario_required
def detalhes_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    return render_template('funcionario/detalhes_produto.html', produto=produto)

# NOVA ROTA: Adicionar produto
@funcionario_bp.route('/funcionario/produtos/novo', methods=['GET', 'POST'])
@funcionario_required
def novo_produto():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        preco = float(request.form.get('preco'))
        categoria = request.form.get('categoria')
        
        # Novos campos
        peso = None
        if request.form.get('peso'):
            try:
                peso = float(request.form.get('peso'))
            except ValueError:
                flash('Valor de peso inválido!', 'danger')
        
        ingredientes = request.form.get('ingredientes')
        
        # Processamento da data de validade
        data_validade = None
        data_validade_str = request.form.get('data_validade')
        if data_validade_str:
            try:
                data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d')
            except ValueError:
                flash('Formato de data de validade inválido!', 'danger')
        
        informacoes_nutricionais = request.form.get('informacoes_nutricionais')
        
        imagem = None
        
        if 'imagem' in request.files:
            arquivo = request.files['imagem']
            if arquivo.filename != '':
                if allowed_file(arquivo.filename):
                    filename = secure_filename(arquivo.filename)
                    
                    # Criar diretório se não existir
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Salvar o arquivo
                    arquivo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    imagem = '/static/uploads/' + filename
        
        novo_produto = Produto(
            nome=nome,
            descricao=descricao,
            preco=preco,
            categoria=categoria,
            imagem=imagem,
            peso=peso,
            ingredientes=ingredientes,
            data_validade=data_validade,
            informacoes_nutricionais=informacoes_nutricionais,
            ativo=True
        )
        
        db.session.add(novo_produto)
        db.session.commit()
        
        # Registrar log
        registrar_log(
            tipo='produto_novo',
            descricao=f'Produto "{nome}" (ID: {novo_produto.id}) adicionado por funcionário',
            usuario_id=session['usuario_id']
        )
        
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('funcionario.produtos'))
    
    return render_template('funcionario/novo_produto.html')

# NOVA ROTA: Editar produto
@funcionario_bp.route('/funcionario/produtos/editar/<int:produto_id>', methods=['GET', 'POST'])
@funcionario_required
def editar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    
    if request.method == 'POST':
        produto.nome = request.form.get('nome')
        produto.descricao = request.form.get('descricao')
        
        # Validação de preço
        preco_str = request.form.get('preco')
        if preco_str:
            try:
                produto.preco = float(preco_str)
            except (ValueError, TypeError):
                flash('Valor de preço inválido!', 'danger')
                return render_template('funcionario/editar_produto.html', produto=produto)
        else:
            flash('O preço é obrigatório!', 'danger')
            return render_template('funcionario/editar_produto.html', produto=produto)
        
        produto.categoria = request.form.get('categoria')
        
        # Novos campos
        produto.peso = None
        if request.form.get('peso'):
            try:
                produto.peso = float(request.form.get('peso'))
            except ValueError:
                flash('Valor de peso inválido!', 'danger')
                return render_template('funcionario/editar_produto.html', produto=produto)
        
        produto.ingredientes = request.form.get('ingredientes')
        
        # Validação de data
        data_validade_str = request.form.get('data_validade')
        if data_validade_str:
            try:
                data_validade = datetime.strptime(data_validade_str, '%d/%m/%Y').date()
                
                # Validação: não permitir data no passado
                if data_validade < date.today():
                    flash('A data de validade não pode ser anterior a hoje!', 'danger')
                    return render_template('funcionario/editar_produto.html', produto=produto)
                
                produto.data_validade = datetime.strptime(data_validade_str, '%d/%m/%Y')
            except ValueError:
                flash('Formato de data de validade inválido!', 'danger')
                return render_template('funcionario/editar_produto.html', produto=produto)
        else:
            produto.data_validade = None
        
        produto.informacoes_nutricionais = request.form.get('informacoes_nutricionais')
        
        # Upload da imagem (se fornecida)
        if 'imagem' in request.files:
            arquivo = request.files['imagem']
            if arquivo.filename != '':
                if allowed_file(arquivo.filename):
                    filename = secure_filename(arquivo.filename)
                    
                    # Criar diretório se não existir
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Salvar o arquivo
                    arquivo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    produto.imagem = '/static/uploads/' + filename
        
        produto.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        # Registrar log
        registrar_log(
            tipo='produto_atualizado',
            descricao=f'Produto "{produto.nome}" (ID: {produto.id}) atualizado por funcionário',
            usuario_id=session['usuario_id']
        )
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('funcionario.produtos'))
    
    return render_template('funcionario/editar_produto.html', produto=produto)

# NOVA ROTA: Desativar produto (soft delete)
@funcionario_bp.route('/funcionario/produtos/deletar/<int:produto_id>', methods=['POST'])
@funcionario_required
def deletar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    
    try:
        # Soft delete - marcar como inativo
        produto.ativo = False
        produto.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        # Registrar log
        registrar_log(
            tipo='produto_desativado',
            descricao=f'Produto "{produto.nome}" (ID: {produto.id}) desativado por funcionário',
            usuario_id=session.get('usuario_id')
        )
        
        flash(f'Produto "{produto.nome}" foi desativado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desativar produto: {str(e)}', 'danger')
    
    return redirect(url_for('funcionario.produtos'))

# NOVA ROTA: Reativar produto
@funcionario_bp.route('/funcionario/produtos/reativar/<int:produto_id>', methods=['POST'])
@funcionario_required
def reativar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    
    try:
        produto.ativo = True
        produto.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        # Registrar log
        registrar_log(
            tipo='produto_reativado',
            descricao=f'Produto "{produto.nome}" (ID: {produto.id}) reativado por funcionário',
            usuario_id=session.get('usuario_id')
        )
        
        flash(f'Produto "{produto.nome}" foi reativado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao reativar produto: {str(e)}', 'danger')
    
    return redirect(url_for('funcionario.produtos'))

# ==================== ROTAS DE CLIENTES ====================

@funcionario_bp.route('/funcionario/clientes')
@funcionario_required
def clientes():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    busca = request.args.get('busca', '')
    
    query = Usuario.query.filter_by(is_admin=False, is_funcionario=False)
    
    if busca:
        query = query.filter(
            (Usuario.nome.ilike(f'%{busca}%')) | 
            (Usuario.email.ilike(f'%{busca}%'))
        )
    
    # Criar subquery para contar pedidos
    from sqlalchemy import func
    pedidos_count = db.session.query(
        Pedido.usuario_id, 
        func.count(Pedido.id).label('total_pedidos')
    ).group_by(Pedido.usuario_id).subquery()
    
    query = query.outerjoin(
        pedidos_count, 
        Usuario.id == pedidos_count.c.usuario_id
    ).add_columns(
        func.coalesce(pedidos_count.c.total_pedidos, 0).label('total_pedidos')
    )
    
    clientes_paginados = query.order_by(Usuario.nome).paginate(page=page, per_page=per_page)
    
    clientes = []
    for cliente, total_pedidos in clientes_paginados.items:
        cliente.total_pedidos = total_pedidos
        clientes.append(cliente)
    
    from collections import namedtuple
    Pagination = namedtuple('Pagination', ['items', 'page', 'per_page', 'total', 'has_prev', 'has_next', 'prev_num', 'next_num', 'iter_pages'])
    
    clientes_resultado = Pagination(
        items=clientes,
        page=clientes_paginados.page,
        per_page=clientes_paginados.per_page,
        total=clientes_paginados.total,
        has_prev=clientes_paginados.has_prev,
        has_next=clientes_paginados.has_next,
        prev_num=clientes_paginados.prev_num,
        next_num=clientes_paginados.next_num,
        iter_pages=clientes_paginados.iter_pages
    )
    
    return render_template('funcionario/clientes.html', clientes=clientes_resultado)

@funcionario_bp.route('/funcionario/clientes/<int:cliente_id>')
@funcionario_required
def ver_cliente(cliente_id):
    cliente = Usuario.query.filter_by(id=cliente_id, is_admin=False, is_funcionario=False).first_or_404()
    
    # Buscar pedidos do cliente
    pedidos = Pedido.query.filter_by(usuario_id=cliente_id).order_by(Pedido.data.desc()).all()
    
    return render_template('funcionario/ver_cliente.html', cliente=cliente, pedidos=pedidos)