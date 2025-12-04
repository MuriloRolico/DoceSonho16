from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from database import db
from models.models import Produto, Log, Pedido, ItemPedido, ItemPedidoPersonalizado, BoloPersonalizado, Usuario
from datetime import datetime, timedelta, date
from werkzeug.utils import secure_filename
import os
from utils.helpers import is_admin, allowed_file, registrar_log
 

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin/dashboard.html')

# Rotas para gerenciamento de usuários (administradores)
@admin_bp.route('/admin/usuarios')
def admin_usuarios():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    # Buscar apenas usuários que são administradores
    usuarios = Usuario.query.filter_by(is_admin=True).all()
    
    return render_template('admin/usuarios.html', usuarios=usuarios)

# Rotas para gerenciamento de clientes
@admin_bp.route('/admin/clientes')
def admin_clientes():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    busca = request.args.get('busca', '')
    
    query = Usuario.query.filter_by(is_admin=False)
    
    if busca:
        query = query.filter(
            (Usuario.nome.ilike(f'%{busca}%')) | 
            (Usuario.email.ilike(f'%{busca}%'))
        )
    
    # Criar uma subquery para contar pedidos por cliente
    from sqlalchemy import func
    pedidos_count = db.session.query(
        Pedido.usuario_id, 
        func.count(Pedido.id).label('total_pedidos')
    ).group_by(Pedido.usuario_id).subquery()
    
    # Adicionar a contagem de pedidos à query principal
    query = query.outerjoin(
        pedidos_count, 
        Usuario.id == pedidos_count.c.usuario_id
    ).add_columns(
        func.coalesce(pedidos_count.c.total_pedidos, 0).label('total_pedidos')
    )
    
    # Paginar os resultados
    clientes_paginados = query.order_by(Usuario.nome).paginate(page=page, per_page=per_page)
    
    # Criar uma lista de objetos compostos com os dados dos clientes e contagem de pedidos
    clientes = []
    for cliente, total_pedidos in clientes_paginados.items:
        cliente.total_pedidos = total_pedidos
        clientes.append(cliente)
    
    # Criar um objeto de paginação com os mesmos atributos do original
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
    
    return render_template('admin/clientes.html', clientes=clientes_resultado)

@admin_bp.route('/admin/clientes/<int:cliente_id>')
def admin_ver_cliente(cliente_id):
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    cliente = Usuario.query.filter_by(id=cliente_id, is_admin=False).first_or_404()
    
    # Buscar pedidos do cliente
    pedidos = Pedido.query.filter_by(usuario_id=cliente_id).order_by(Pedido.data.desc()).all()
    
    return render_template('admin/ver_cliente.html', cliente=cliente, pedidos=pedidos)

@admin_bp.route('/admin/usuarios/novo', methods=['GET', 'POST'])
def admin_novo_usuario():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    tipo = request.args.get('tipo', 'admin')  # 'admin' ou 'cliente'
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Verificar se o email já existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este email já está em uso.', 'danger')
            return render_template('admin/novo_usuario.html', tipo=tipo)
        
        # Determinar se é admin baseado no tipo
        is_admin_value = tipo == 'admin'
        
        # Criar novo usuário
        from werkzeug.security import generate_password_hash
        
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            is_admin=is_admin_value,
            status='ativo',
            concordou_politica=True
        )
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        # Registrar log
        registrar_log(
            tipo='usuario_novo',
            descricao=f'Novo {"administrador" if is_admin_value else "cliente"} "{nome}" (ID: {novo_usuario.id}) criado por administrador',
            usuario_id=session['usuario_id']
        )
        
        flash(f'{"Administrador" if is_admin_value else "Cliente"} adicionado com sucesso!', 'success')
        
        if is_admin_value:
            return redirect(url_for('admin.admin_usuarios'))
        else:
            return redirect(url_for('admin.admin_clientes'))
    
    return render_template('admin/novo_usuario.html', tipo=tipo)

@admin_bp.route('/admin/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
def admin_editar_usuario(usuario_id):
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if request.method == 'POST':
        usuario.nome = request.form.get('nome')
        
        # Verificar se o email foi alterado e se já existe
        novo_email = request.form.get('email')
        if novo_email != usuario.email:
            usuario_existente = Usuario.query.filter_by(email=novo_email).first()
            if usuario_existente:
                flash('Este email já está em uso por outro usuário.', 'danger')
                return render_template('admin/editar_usuario.html', usuario=usuario)
            usuario.email = novo_email
        
        # Atualizar senha se fornecida
        nova_senha = request.form.get('senha')
        if nova_senha:
            from werkzeug.security import generate_password_hash
            usuario.senha = generate_password_hash(nova_senha)
        
        # Atualizar outros campos específicos para clientes
        if not usuario.is_admin:
            usuario.endereco_cep = request.form.get('cep')
            usuario.endereco_rua = request.form.get('rua')
            usuario.endereco_numero = request.form.get('numero')
            usuario.endereco_complemento = request.form.get('complemento')
            usuario.endereco_bairro = request.form.get('bairro')
            usuario.endereco_cidade = request.form.get('cidade')
            usuario.endereco_estado = request.form.get('estado')
        
        db.session.commit()
        
        # Registrar log de atualização
        registrar_log(
            tipo='usuario_atualizado',
            descricao=f'{"Administrador" if usuario.is_admin else "Cliente"} "{usuario.nome}" (ID: {usuario.id}) atualizado por administrador',
            usuario_id=session['usuario_id']
        )
        
        flash('Usuário atualizado com sucesso!', 'success')
        
        if usuario.is_admin:
            return redirect(url_for('admin.admin_usuarios'))
        else:
            return redirect(url_for('admin.admin_clientes'))
    
    return render_template('admin/editar_usuario.html', usuario=usuario)

@admin_bp.route('/admin/usuarios/status/<int:usuario_id>', methods=['POST'])
def admin_alterar_status_usuario(usuario_id):
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Não permitir alterar o status do próprio usuário logado
    if usuario.id == session.get('usuario_id'):
        flash('Você não pode alterar seu próprio status!', 'danger')
        if usuario.is_admin:
            return redirect(url_for('admin.admin_usuarios'))
        else:
            return redirect(url_for('admin.admin_clientes'))
    
    novo_status = request.form.get('novo_status')
    
    if novo_status in ['ativo', 'inativo']:
        usuario.status = novo_status
        db.session.commit()
        
        # Registrar log de alteração de status
        registrar_log(
            tipo='usuario_status',
            descricao=f'Status do {"administrador" if usuario.is_admin else "cliente"} "{usuario.nome}" (ID: {usuario.id}) alterado para {novo_status}',
            usuario_id=session['usuario_id']
        )
        
        flash(f'Status do usuário alterado para: {novo_status}', 'success')
    
    if usuario.is_admin:
        return redirect(url_for('admin.admin_usuarios'))
    else:
        return redirect(url_for('admin.admin_clientes'))

@admin_bp.route('/admin/logs')
def admin_logs():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = Log.query.order_by(Log.data.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/admin/logs/filtrar', methods=['GET'])
def filtrar_logs():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    tipo = request.args.get('tipo')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    usuario_id = request.args.get('usuario_id')
    
    query = Log.query
    
    if tipo:
        query = query.filter(Log.tipo == tipo)
    
    if data_inicio:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        query = query.filter(Log.data >= data_inicio)
    
    if data_fim:
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Log.data <= data_fim)
    
    if usuario_id:
        query = query.filter(Log.usuario_id == usuario_id)
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = query.order_by(Log.data.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/logs.html', logs=logs, filtros=request.args)

# ROTAS DE PEDIDOS - SEÇÃO COMPLETA
@admin_bp.route('/admin/pedidos')
def admin_pedidos():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    status = request.args.get('status', '')
    
    query = Pedido.query
    
    if status:
        query = query.filter(Pedido.status == status)
    
    pedidos = query.order_by(Pedido.data.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/pedidos.html', pedidos=pedidos, status_atual=status)

@admin_bp.route('/admin/pedido/<int:pedido_id>')
def admin_detalhes_pedido(pedido_id):
    if not is_admin():
        
        return redirect(url_for('index'))
    
    pedido = Pedido.query.get_or_404(pedido_id)
    usuario = Usuario.query.get(pedido.usuario_id)
    
    # Obter itens regulares
    itens_regulares = ItemPedido.query.filter_by(pedido_id=pedido.id).all()
    
    detalhes_itens_regulares = []
    for item in itens_regulares:
        produto = Produto.query.get(item.produto_id)
        
        # Verificar se o produto ainda existe (mesmo que inativo)
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
            'produto': produto  # Adicionar o objeto completo para acessar outras informações
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
            'bolo': bolo  # Adicionar o objeto completo para acessar detalhes
        })
    
    # Combinar os dois tipos de itens
    todos_itens = detalhes_itens_regulares + detalhes_itens_personalizados
    
    # Obtém histórico de atualizações de status, se existir
    historico_status = Log.query.filter(
        Log.tipo == 'pedido_atualizado',
        Log.descricao.like(f'Pedido #{pedido.id} atualizado%')
    ).order_by(Log.data.desc()).all()
    
    return render_template('admin/detalhes_pedido.html', 
                          pedido=pedido, 
                          itens=todos_itens, 
                          usuario=usuario,
                          historico_status=historico_status)

@admin_bp.route('/admin/pedido/<int:pedido_id>/atualizar', methods=['GET', 'POST'])
def admin_atualizar_pedido(pedido_id):
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    pedido = Pedido.query.get_or_404(pedido_id)
    usuario = Usuario.query.get(pedido.usuario_id)
    
    # PROTEÇÃO: Verificar se o pedido está cancelado
    if pedido.status == 'Cancelado':
        flash('Este pedido está cancelado e não pode mais ser alterado. Esta é uma ação irreversível.', 'danger')
        return redirect(url_for('admin.admin_detalhes_pedido', pedido_id=pedido.id))
    
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
            descricao = f'Pedido #{pedido.id} atualizado de "{status_anterior}" para "{novo_status}" por administrador'
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
            
            return redirect(url_for('admin.admin_detalhes_pedido', pedido_id=pedido.id))
    
    # Se for GET ou se ocorrer algum erro no POST, mostrar a página de atualização
    
    # Obter histórico de status para exibir
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
    
    return render_template('admin/atualizar_pedido.html', 
                          pedido=pedido, 
                          itens=todos_itens,
                          usuario=usuario,
                          historico_status=historico_status)
@admin_bp.route('/admin/produtos')
def admin_produtos():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    # Separar produtos ativos e inativos
    produtos_ativos = Produto.ativos().all()
    produtos_inativos = Produto.inativos().all()
    
    return render_template('admin/produtos.html', 
                         produtos_ativos=produtos_ativos,
                         produtos_inativos=produtos_inativos)

@admin_bp.route('/admin/produtos/novo', methods=['GET', 'POST'])
def admin_novo_produto():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
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
            ativo=True  # Novo produto sempre ativo
        )
        
        db.session.add(novo_produto)
        db.session.commit()
        
        # Registrar log de novo produto
        registrar_log(
            tipo='produto_novo',
            descricao=f'Produto "{nome}" (ID: {novo_produto.id}) adicionado por administrador',
            usuario_id=session['usuario_id']
        )
        
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('admin.admin_produtos'))
    
    return render_template('admin/novo_produto.html')

@admin_bp.route('/admin/produtos/editar/<int:produto_id>', methods=['GET', 'POST'])
def admin_editar_produto(produto_id):
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    
    
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
                return render_template('admin/editar_produto.html', produto=produto)
        else:
            flash('O preço é obrigatório!', 'danger')
            return render_template('admin/editar_produto.html', produto=produto)
        
        produto.categoria = request.form.get('categoria')
        
        # Novos campos
        produto.peso = None
        if request.form.get('peso'):
            try:
                produto.peso = float(request.form.get('peso'))
            except ValueError:
                flash('Valor de peso inválido!', 'danger')
                return render_template('admin/editar_produto.html', produto=produto)
        
        produto.ingredientes = request.form.get('ingredientes')
        
        # Validação de data
        data_validade_str = request.form.get('data_validade')
        if data_validade_str:
            try:
                data_validade = datetime.strptime(data_validade_str, '%d/%m/%Y').date()
                
                # Validação: não permitir data no passado
                if data_validade < date.today():
                    flash('A data de validade não pode ser anterior a hoje!', 'danger')
                    return render_template('admin/editar_produto.html', produto=produto)
                
                produto.data_validade = datetime.strptime(data_validade_str, '%d/%m/%Y')
            except ValueError:
                flash('Formato de data de validade inválido!', 'danger')
                return render_template('admin/editar_produto.html', produto=produto)
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
        
        # Registrar log de atualização
        registrar_log(
            tipo='produto_atualizado',
            descricao=f'Produto "{produto.nome}" (ID: {produto.id}) atualizado por administrador',
            usuario_id=session['usuario_id']
        )
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin.admin_produtos'))
    

    
    
    
    return render_template('admin/editar_produto.html', produto=produto)

@admin_bp.route('/admin/produtos/deletar/<int:produto_id>', methods=['POST'])
def admin_deletar_produto(produto_id):
    """Soft delete - desativar produto em vez de excluir"""
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    produto = Produto.query.get_or_404(produto_id)
    
    try:
        # Soft delete - marcar como inativo
        produto.ativo = False
        produto.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        # Registrar log da ação
        registrar_log(
            tipo='produto_desativado',
            descricao=f'Produto "{produto.nome}" (ID: {produto.id}) desativado por administrador',
            usuario_id=session.get('usuario_id')
        )
        
        flash(f'Produto "{produto.nome}" foi desativado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desativar produto: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin_produtos'))

@admin_bp.route('/admin/produtos/reativar/<int:produto_id>', methods=['POST'])
def admin_reativar_produto(produto_id):
    """Reativar produto desativado"""
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    produto = Produto.query.get_or_404(produto_id)
    
    try:
        produto.ativo = True
        produto.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        # Registrar log da ação
        registrar_log(
            tipo='produto_reativado',
            descricao=f'Produto "{produto.nome}" (ID: {produto.id}) reativado por administrador',
            usuario_id=session.get('usuario_id')
        )
        
        flash(f'Produto "{produto.nome}" foi reativado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao reativar produto: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin_produtos'))

@admin_bp.route('/admin/produtos/deletar-permanente/<int:produto_id>', methods=['POST'])
def admin_deletar_produto_permanente(produto_id):
    """Exclusão permanente apenas para produtos que nunca foram vendidos"""
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    produto = Produto.query.get_or_404(produto_id)
    
    try:
        # Verificar se o produto tem pedidos associados
        items_associados = ItemPedido.query.filter_by(produto_id=produto_id).first()
        
        if items_associados:
            flash('Não é possível excluir permanentemente este produto pois ele está associado a pedidos existentes. Use a desativação em vez disso.', 'danger')
            return redirect(url_for('admin.admin_produtos'))
        
        # Remover imagem se existir
        if produto.imagem and produto.imagem.startswith('/static/uploads/'):
            try:
                caminho_imagem = os.path.join(current_app.root_path, produto.imagem.lstrip('/'))
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
            except Exception as e:
                print(f"Erro ao excluir imagem: {e}")
        
        nome_produto = produto.nome
        produto_id_log = produto.id
        
        # Excluir permanentemente do banco de dados
        db.session.delete(produto)
        db.session.commit()
        
        # Registrar log da exclusão permanente
        registrar_log(
            tipo='produto_excluido_permanente',
            descricao=f'Produto "{nome_produto}" (ID: {produto_id_log}) excluído permanentemente por administrador',
            usuario_id=session.get('usuario_id')
        )
        
        flash(f'Produto "{nome_produto}" foi excluído permanentemente!', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir produto permanentemente: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin_produtos'))