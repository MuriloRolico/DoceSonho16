from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, current_app
from database import db
from models.models import Usuario, Pedido, BoloPersonalizado, ItemPedido, ItemPedidoPersonalizado, Produto
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file
import os
import json
import io
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para acessar seu perfil', 'warning')
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get_or_404(session['usuario_id'])
    return render_template('perfil.html', usuario=usuario)

@user_bp.route('/perfil/atualizar', methods=['POST'])
def atualizar_perfil():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para atualizar seu perfil', 'warning')
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get_or_404(session['usuario_id'])
    
    # Obter dados do formulário
    nome = request.form.get('nome')
    email = request.form.get('email')
    
    # Verificar se o email já existe para outro usuário
    if email != usuario.email:
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este e-mail já está sendo utilizado por outra conta', 'danger')
            return redirect(url_for('user.perfil'))
    
    # Atualizar dados
    usuario.nome = nome
    usuario.email = email
    
    db.session.commit()
    flash('Perfil atualizado com sucesso!', 'success')
    return redirect(url_for('user.perfil'))

@user_bp.route('/perfil/foto', methods=['POST'])
def atualizar_foto():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para atualizar sua foto', 'warning')
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get_or_404(session['usuario_id'])
    
    # Verificar se há um arquivo de foto no formulário
    if 'foto_perfil' not in request.files:
        flash('Nenhuma foto foi enviada', 'danger')
        return redirect(url_for('user.perfil'))
    
    arquivo = request.files['foto_perfil']
    
    if arquivo.filename == '':
        flash('Nenhuma foto foi selecionada', 'danger')
        return redirect(url_for('user.perfil'))
    
    if not allowed_file(arquivo.filename):
        flash('Formato de arquivo não permitido. Use JPG, JPEG, PNG ou GIF', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Limitar tamanho do arquivo (5MB)
    if len(arquivo.read()) > 5 * 1024 * 1024:
        flash('O arquivo é muito grande. O tamanho máximo permitido é 5MB', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Resetar o ponteiro do arquivo
    arquivo.seek(0)
    
    # Criar uma pasta para fotos de perfil se não existir
    diretorio_uploads = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pics')
    os.makedirs(diretorio_uploads, exist_ok=True)
    
    # Salvar a foto com um nome seguro que inclui o ID do usuário
    filename = f"user_{usuario.id}_{secure_filename(arquivo.filename)}"
    arquivo.save(os.path.join(diretorio_uploads, filename))
    
    # Excluir foto antiga se existir
    if usuario.foto_perfil and usuario.foto_perfil.startswith('/static/uploads/profile_pics/'):
        try:
            caminho_foto_antiga = os.path.join(current_app.root_path, usuario.foto_perfil.lstrip('/'))
            if os.path.exists(caminho_foto_antiga):
                os.remove(caminho_foto_antiga)
        except Exception as e:
            print(f"Erro ao excluir foto antiga: {e}")
    
    # Atualizar o caminho da foto no banco de dados
    usuario.foto_perfil = f'/static/uploads/profile_pics/{filename}'
    
    db.session.commit()
    flash('Foto de perfil atualizada com sucesso!', 'success')
    return redirect(url_for('user.perfil'))

@user_bp.route('/perfil/alterar-senha', methods=['POST'])
def alterar_senha():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para alterar sua senha', 'warning')
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get_or_404(session['usuario_id'])
    
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')
    confirmar_nova_senha = request.form.get('confirmar_nova_senha')
    
    # Verificar se a senha atual está correta
    if not check_password_hash(usuario.senha, senha_atual):
        flash('Senha atual incorreta', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar se as novas senhas coincidem
    if nova_senha != confirmar_nova_senha:
        flash('As novas senhas não coincidem', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar requisitos de segurança da senha
    import re
    if len(nova_senha) < 8:
        flash('A senha deve ter pelo menos 8 caracteres', 'danger')
        return redirect(url_for('user.perfil'))
    if not re.search("[a-z]", nova_senha):
        flash('A senha deve conter pelo menos uma letra minúscula', 'danger')
        return redirect(url_for('user.perfil'))
    if not re.search("[A-Z]", nova_senha):
        flash('A senha deve conter pelo menos uma letra maiúscula', 'danger')
        return redirect(url_for('user.perfil'))
    if not re.search("[0-9]", nova_senha):
        flash('A senha deve conter pelo menos um número', 'danger')
        return redirect(url_for('user.perfil'))
    if not re.search("[_@$!%*?&]", nova_senha):
        flash('A senha deve conter pelo menos um caractere especial', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Atualizar a senha
    usuario.senha = generate_password_hash(nova_senha)
    
    db.session.commit()
    flash('Senha alterada com sucesso!', 'success')
    return redirect(url_for('user.perfil'))

@user_bp.route('/perfil/excluir', methods=['POST'])
def excluir_conta():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para excluir sua conta', 'warning')
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get_or_404(session['usuario_id'])
    
    # Verificar confirmação
    confirmar_exclusao = request.form.get('confirmar_exclusao')
    if not confirmar_exclusao:
        flash('Você precisa confirmar a exclusão da conta', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar senha
    senha = request.form.get('confirmar_senha')
    if not check_password_hash(usuario.senha, senha):
        flash('Senha incorreta', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Excluir foto de perfil se existir
    if usuario.foto_perfil and usuario.foto_perfil.startswith('/static/uploads/profile_pics/'):
        try:
            caminho_foto = os.path.join(current_app.root_path, usuario.foto_perfil.lstrip('/'))
            if os.path.exists(caminho_foto):
                os.remove(caminho_foto)
        except Exception as e:
            print(f"Erro ao excluir foto de perfil: {e}")
    
    # Implementação de anonimização/exclusão conforme LGPD
    try:
        # Anonimizar dados do usuário em vez de excluir completamente
        usuario.nome = f"Usuário Excluído {usuario.id}"
        usuario.email = f"excluido_{usuario.id}@anonimo.com"
        usuario.senha = "excluido"
        usuario.foto_perfil = None
        
        # Marcar o usuário como inativo ou excluído
        # Você pode adicionar um campo 'ativo' na tabela Usuario para controlar isso
        
        # Encerrar a sessão do usuário
        session.pop('usuario_id', None)
        session.pop('carrinho', None)
        session.pop('carrinho_personalizado', None)
        
        db.session.commit()
        flash('Sua conta foi excluída com sucesso. Esperamos vê-lo novamente em breve!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir conta: {str(e)}', 'danger')
        return redirect(url_for('user.perfil'))
    
    return redirect(url_for('index'))

@user_bp.route('/perfil/dados-pessoais')
def dados_pessoais():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para acessar seus dados pessoais', 'warning')
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get_or_404(session['usuario_id'])
    
    # Buscar pedidos do usuário
    pedidos = Pedido.query.filter_by(usuario_id=usuario.id).order_by(Pedido.data.desc()).all()
    
    # Buscar bolos personalizados do usuário
    bolos_personalizados = BoloPersonalizado.query.filter_by(usuario_id=usuario.id, ativo=True).all()
    
    return render_template('dados_pessoais.html', usuario=usuario, pedidos=pedidos, bolos_personalizados=bolos_personalizados)

@user_bp.route('/perfil/exportar-dados')
def exportar_dados():
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para exportar seus dados', 'warning')
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get_or_404(session['usuario_id'])
    
    # Preparar dados do usuário (excluindo a senha por segurança)
    dados_usuario = {
        'id': usuario.id,
        'nome': usuario.nome,
        'email': usuario.email,
        'data_registro': usuario.data_registro.strftime('%Y-%m-%d %H:%M:%S'),
        'is_admin': usuario.is_admin
    }
    
    # Buscar pedidos do usuário
    pedidos_usuario = []
    pedidos = Pedido.query.filter_by(usuario_id=usuario.id).all()
    
    for pedido in pedidos:
        itens_regulares = []
        for item in ItemPedido.query.filter_by(pedido_id=pedido.id).all():
            produto = Produto.query.get(item.produto_id)
            itens_regulares.append({
                'produto': produto.nome,
                'quantidade': item.quantidade,
                'preco_unitario': float(item.preco_unitario),
                'subtotal': float(item.preco_unitario * item.quantidade)
            })
        
        itens_personalizados = []
        for item in ItemPedidoPersonalizado.query.filter_by(pedido_id=pedido.id).all():
            bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
            itens_personalizados.append({
                'tipo': 'Bolo Personalizado',
                'massa': bolo.massa,
                'quantidade': item.quantidade,
                'preco_unitario': float(item.preco_unitario),
                'subtotal': float(item.preco_unitario * item.quantidade)
            })
        
        pedidos_usuario.append({
            'id': pedido.id,
            'data': pedido.data.strftime('%Y-%m-%d %H:%M:%S'),
            'status': pedido.status,
            'total': float(pedido.total),
            'itens_regulares': itens_regulares,
            'itens_personalizados': itens_personalizados
        })
    
    # Buscar bolos personalizados do usuário
    bolos_personalizados_usuario = []
    bolos = BoloPersonalizado.query.filter_by(usuario_id=usuario.id).all()
    
    for bolo in bolos:
        bolos_personalizados_usuario.append({
            'id': bolo.id,
            'nome': bolo.nome,
            'massa': bolo.massa,
            'recheios': json.loads(bolo.recheios),
            'cobertura': bolo.cobertura,
            'finalizacao': json.loads(bolo.finalizacao) if bolo.finalizacao else [],
            'observacoes': bolo.observacoes,
            'preco': float(bolo.preco),
            'data_criacao': bolo.data_criacao.strftime('%Y-%m-%d %H:%M:%S'),
            'ativo': bolo.ativo
        })
    
    # Agrupar todos os dados
    dados_completos = {
        'usuario': dados_usuario,
        'pedidos': pedidos_usuario,
        'bolos_personalizados': bolos_personalizados_usuario,
        'data_exportacao': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Retornar como um download de arquivo JSON
    arquivo_json = io.BytesIO()
    arquivo_json.write(json.dumps(dados_completos, indent=4, ensure_ascii=False).encode('utf-8'))
    arquivo_json.seek(0)
    
    return send_file(
        arquivo_json,
        as_attachment=True,
        download_name=f'dados_doce_sonho_usuario_{usuario.id}.json',
        mimetype='application/json'
    )