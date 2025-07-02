from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from database import db
from models.models import Produto, Log, Pedido, ItemPedido, ItemPedidoPersonalizado, BoloPersonalizado, Usuario
from datetime import datetime, timedelta
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
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    pedido = Pedido.query.get_or_404(pedido_id)
    usuario = Usuario.query.get(pedido.usuario_id)
    
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
    
    return render_template('admin/detalhes_pedido.html', pedido=pedido, itens=todos_itens, usuario=usuario)

@admin_bp.route('/admin/pedido/<int:pedido_id>/atualizar', methods=['POST'])
def admin_atualizar_pedido(pedido_id):
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    pedido = Pedido.query.get_or_404(pedido_id)
    
    status_anterior = pedido.status
    novo_status = request.form.get('status')
    
    if novo_status and novo_status != status_anterior:
        pedido.status = novo_status
        db.session.commit()
        
        # Registrar o log de atualização
        registrar_log(
            tipo='pedido_atualizado',
            descricao=f'Pedido #{pedido.id} atualizado de "{status_anterior}" para "{novo_status}"',
            usuario_id=session.get('usuario_id')
        )
        
        flash(f'Status do pedido atualizado para: {novo_status}', 'success')
    
    return redirect(url_for('admin.admin_detalhes_pedido', pedido_id=pedido.id))

@admin_bp.route('/admin/produtos')
def admin_produtos():
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    produtos = Produto.query.all()
    return render_template('admin/produtos.html', produtos=produtos)

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
            informacoes_nutricionais=informacoes_nutricionais
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
        produto.preco = float(request.form.get('preco'))
        produto.categoria = request.form.get('categoria')
        
        # Novos campos
        produto.peso = None
        if request.form.get('peso'):
            try:
                produto.peso = float(request.form.get('peso'))
            except ValueError:
                flash('Valor de peso inválido!', 'danger')
        
        produto.ingredientes = request.form.get('ingredientes')
        
       
        data_validade_str = request.form.get('data_validade')
        if data_validade_str:
            try:
                produto.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d')
            except ValueError:
                flash('Formato de data de validade inválido!', 'danger')
        
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
        
        db.session.commit()
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin.admin_produtos'))
    
    return render_template('admin/editar_produto.html', produto=produto)

@admin_bp.route('/admin/produtos/deletar/<int:produto_id>', methods=['POST'])
def admin_deletar_produto(produto_id):
    if not is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    produto = Produto.query.get_or_404(produto_id)
    
    try:
     
        items_associados = ItemPedido.query.filter_by(produto_id=produto_id).first()
        
        if items_associados:
            flash('Não é possível excluir este produto pois ele está associado a pedidos existentes.', 'danger')
            return redirect(url_for('admin.admin_produtos'))
        
   
        if produto.imagem and produto.imagem.startswith('/static/uploads/'):
            try:
                caminho_imagem = os.path.join(current_app.root_path, produto.imagem.lstrip('/'))
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
            except Exception as e:
                # Registre o erro, mas continue com a exclusão do produto
                print(f"Erro ao excluir imagem: {e}")
        
        # Excluir o produto do banco de dados
        db.session.delete(produto)
        db.session.commit()
        
        flash('Produto excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir produto: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin_produtos'))