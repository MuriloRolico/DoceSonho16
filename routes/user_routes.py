from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, current_app
from database import db
from models.models import Usuario, Pedido, BoloPersonalizado, ItemPedido, ItemPedidoPersonalizado, Produto, Token
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file
from datetime import datetime, timedelta
import os
import json
import io
import uuid
import re
from functools import wraps

user_bp = Blueprint('user', __name__)

# Decorator para proteger rotas que exigem autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa fazer login para acessar esta página', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/perfil')
@login_required
def perfil():
    usuario = db.session.get(Usuario, session['usuario_id'])
    # Buscar tokens ativos para exibir nas sessões
    tokens = Token.query.filter_by(usuario_id=usuario.id, is_revogado=False).all()
    return render_template('perfil.html', usuario=usuario, tokens=tokens)

@user_bp.route('/perfil/atualizar', methods=['POST'])
@login_required
def atualizar_perfil():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    # Debug: Imprimir todos os dados do formulário
    print("=== DEBUG: Dados recebidos do formulário ===")
    for key, value in request.form.items():
        print(f"{key}: '{value}'")
    print("==========================================")
    
    # Identificar qual formulário foi enviado
    if 'nome' in request.form:
        # Formulário de dados básicos
        # Obter dados do formulário com validação mais robusta
        nome = request.form.get('nome')
        email = request.form.get('email')
        
        # Verificar se os campos existem no formulário antes de processar
        if nome is None:
            flash('Campo nome não foi encontrado no formulário', 'danger')
            return redirect(url_for('user.perfil'))
        
        if email is None:
            flash('Campo email não foi encontrado no formulário', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Limpar e validar os dados
        nome = nome.strip() if nome else ''
        email = email.strip() if email else ''
        
        # Debug específico para nome e email
        print(f"Nome após processamento: '{nome}' (length: {len(nome)})")
        print(f"Email após processamento: '{email}' (length: {len(email)})")
        
        # Validar campos obrigatórios
        if not nome or len(nome) == 0:
            flash('O nome é obrigatório e não pode estar vazio', 'danger')
            return redirect(url_for('user.perfil'))
        
        if not email or len(email) == 0:
            flash('O e-mail é obrigatório e não pode estar vazio', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Validar comprimento mínimo do nome
        if len(nome) < 2:
            flash('O nome deve ter pelo menos 2 caracteres', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Validar formato do email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Por favor, insira um e-mail válido', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Verificar se o email já existe para outro usuário
        if email != usuario.email:
            usuario_existente = Usuario.query.filter_by(email=email).first()
            if usuario_existente:
                flash('Este e-mail já está sendo utilizado por outra conta', 'danger')
                return redirect(url_for('user.perfil'))
        
        # Atualizar dados básicos
        usuario.nome = nome
        usuario.email = email
        
    elif 'endereco_cep' in request.form:
        # Formulário de endereço
        # Dados de endereço com validação de existência
        endereco_cep = request.form.get('endereco_cep', '').strip()
        endereco_rua = request.form.get('endereco_rua', '').strip()
        endereco_numero = request.form.get('endereco_numero', '').strip()
        endereco_complemento = request.form.get('endereco_complemento', '').strip()
        endereco_bairro = request.form.get('endereco_bairro', '').strip()
        endereco_cidade = request.form.get('endereco_cidade', '').strip()
        endereco_estado = request.form.get('endereco_estado', '').strip()
        
        # Atualizar dados de endereço (apenas se não estiverem vazios)
        if endereco_cep:
            usuario.endereco_cep = endereco_cep
        if endereco_rua:
            usuario.endereco_rua = endereco_rua
        if endereco_numero:
            usuario.endereco_numero = endereco_numero
        if endereco_complemento:
            usuario.endereco_complemento = endereco_complemento
        if endereco_bairro:
            usuario.endereco_bairro = endereco_bairro
        if endereco_cidade:
            usuario.endereco_cidade = endereco_cidade
        if endereco_estado:
            usuario.endereco_estado = endereco_estado
            
    elif 'mascarar_email' in request.form or 'receber_newsletter' in request.form:
        # Formulário de preferências
        # Preferências de privacidade com verificação de existência
        mascarar_email = request.form.get('mascarar_email') == 'on'
        mascarar_cpf = request.form.get('mascarar_cpf') == 'on'
        mascarar_endereco = request.form.get('mascarar_endereco') == 'on'
        receber_newsletter = request.form.get('receber_newsletter') == 'on'
        receber_sms = request.form.get('receber_sms') == 'on'
        receber_whatsapp = request.form.get('receber_whatsapp') == 'on'
        
        # Atualizar preferências de privacidade (se os campos existirem no modelo)
        if hasattr(usuario, 'mascarar_email'):
            usuario.mascarar_email = mascarar_email
        if hasattr(usuario, 'mascarar_cpf'):
            usuario.mascarar_cpf = mascarar_cpf
        if hasattr(usuario, 'mascarar_endereco'):
            usuario.mascarar_endereco = mascarar_endereco
        if hasattr(usuario, 'receber_newsletter'):
            usuario.receber_newsletter = receber_newsletter
        if hasattr(usuario, 'receber_sms'):
            usuario.receber_sms = receber_sms
        if hasattr(usuario, 'receber_whatsapp'):
            usuario.receber_whatsapp = receber_whatsapp
            
    elif 'cpf' in request.form:
        # Formulário de CPF
        cpf = request.form.get('cpf', '').strip()
        
        # Atualizar CPF se fornecido
        if cpf:
            # Limpar CPF (remover pontos e traços)
            cpf_limpo = cpf.replace('.', '').replace('-', '').replace(' ', '')
            
            # Validar CPF (básico - 11 dígitos)
            if len(cpf_limpo) == 11 and cpf_limpo.isdigit():
                if hasattr(usuario, 'set_cpf'):
                    usuario.set_cpf(cpf_limpo)
                else:
                    # Se não tiver o método set_cpf, definir diretamente
                    usuario.cpf_hash = generate_password_hash(cpf_limpo)
            else:
                flash('CPF inválido. Por favor, insira um CPF válido', 'danger')
                return redirect(url_for('user.perfil'))
    else:
        flash('Formulário não reconhecido', 'danger')
        return redirect(url_for('user.perfil'))
    
    try:
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil: {str(e)}', 'danger')
    
    return redirect(url_for('user.perfil'))

@user_bp.route('/perfil/foto', methods=['POST'])
@login_required
def atualizar_foto():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
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
    
    # Salvar a foto com um nome seguro que inclui o ID do usuário e um UUID para evitar colisões
    filename = f"user_{usuario.id}_{uuid.uuid4()}_{secure_filename(arquivo.filename)}"
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
    
    try:
        db.session.commit()
        flash('Foto de perfil atualizada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar foto: {str(e)}', 'danger')
    
    return redirect(url_for('user.perfil'))

# Modificação em alterar_senha
@user_bp.route('/perfil/alterar-senha', methods=['POST'])
@login_required
def alterar_senha():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    senha_atual = request.form.get('senha_atual', '').strip()
    nova_senha = request.form.get('nova_senha', '').strip()
    confirmar_nova_senha = request.form.get('confirmar_nova_senha', '').strip()
    
    # Validar campos obrigatórios
    if not senha_atual:
        flash('A senha atual é obrigatória', 'danger')
        return redirect(url_for('user.perfil'))
    
    if not nova_senha:
        flash('A nova senha é obrigatória', 'danger')
        return redirect(url_for('user.perfil'))
    
    if not confirmar_nova_senha:
        flash('A confirmação da nova senha é obrigatória', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar se a senha atual está correta
    if not check_password_hash(usuario.senha, senha_atual):
        flash('Senha atual incorreta', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar se as novas senhas coincidem
    if nova_senha != confirmar_nova_senha:
        flash('As novas senhas não coincidem', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar requisitos de segurança da senha
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
    
    try:
        # Revogar todos os tokens existentes por segurança
        tokens = Token.query.filter_by(usuario_id=usuario.id, is_revogado=False).all()
        for token in tokens:
            token.is_revogado = True
        
        db.session.commit()
        
        # Gerar novo token de autenticação se o método existir
        if hasattr(usuario, 'gerar_auth_token'):
            token = usuario.gerar_auth_token()
            session['auth_token'] = token
            
            # Salvar novo token no banco - removendo o IP
            novo_token = Token(
                usuario_id=usuario.id,
                token=token,
                device_info=request.user_agent.string,
                data_expiracao=datetime.utcnow() + timedelta(hours=24)
            )
            db.session.add(novo_token)
            db.session.commit()
        
        flash('Senha alterada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar senha: {str(e)}', 'danger')
    
    return redirect(url_for('user.perfil'))


@user_bp.route('/perfil/revogar-token/<int:token_id>', methods=['POST'])
@login_required
def revogar_token(token_id):
    token = Token.query.get_or_404(token_id)
    
    # Verificar se o token pertence ao usuário atual
    if token.usuario_id != session['usuario_id']:
        flash('Acesso negado', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Não permitir revogar o token atual
    if token.token == session.get('auth_token'):
        flash('Não é possível revogar a sessão atual', 'danger')
        return redirect(url_for('user.perfil'))
    
    try:
        token.is_revogado = True
        db.session.commit()
        flash('Sessão encerrada com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao encerrar sessão: {str(e)}', 'danger')
    
    return redirect(url_for('user.perfil'))

@user_bp.route('/perfil/excluir', methods=['POST'])
@login_required
def excluir_conta():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    # Verificar confirmação
    confirmar_exclusao = request.form.get('confirmar_exclusao')
    if not confirmar_exclusao:
        flash('Você precisa confirmar a exclusão da conta', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar senha
    senha = request.form.get('confirmar_senha', '').strip()
    if not senha:
        flash('A senha é obrigatória para confirmar a exclusão', 'danger')
        return redirect(url_for('user.perfil'))
    
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
        usuario.email = f"excluido_{uuid.uuid4()}@anonimo.com"
        usuario.senha = generate_password_hash(str(uuid.uuid4()))
        usuario.foto_perfil = None
        usuario.cpf_hash = None
        usuario.endereco_cep = None
        usuario.endereco_rua = None
        usuario.endereco_numero = None
        usuario.endereco_complemento = None
        usuario.endereco_bairro = None
        usuario.endereco_cidade = None
        usuario.endereco_estado = None
        if hasattr(usuario, 'status'):
            usuario.status = 'excluido'
        
        # Revogar todos os tokens
        tokens = Token.query.filter_by(usuario_id=usuario.id).all()
        for token in tokens:
            token.is_revogado = True
        
        # Encerrar a sessão do usuário
        session.pop('usuario_id', None)
        session.pop('auth_token', None)
        session.pop('carrinho', None)
        session.pop('carrinho_personalizado', None)
        
        db.session.commit()
        flash('Sua conta foi excluída com sucesso. Esperamos vê-lo novamente em breve!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir conta: {str(e)}', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Limpar cookie
    resposta = redirect(url_for('index'))
    resposta.delete_cookie('auth_token')
    
    return resposta

@user_bp.route('/perfil/dados-pessoais')
@login_required
def dados_pessoais():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    # Buscar pedidos do usuário
    pedidos = Pedido.query.filter_by(usuario_id=usuario.id).order_by(Pedido.data.desc()).all()
    
    # Buscar bolos personalizados do usuário
    bolos_personalizados = BoloPersonalizado.query.filter_by(usuario_id=usuario.id, ativo=True).all()
    
    return render_template('dados_pessoais.html', usuario=usuario, pedidos=pedidos, bolos_personalizados=bolos_personalizados)

@user_bp.route('/perfil/exportar-dados')
@login_required
def exportar_dados():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    # Preparar dados do usuário (excluindo a senha por segurança)
    dados_usuario = {
        'id': usuario.id,
        'nome': usuario.nome,
        'email': usuario.email,
        'data_registro': usuario.data_registro.strftime('%Y-%m-%d %H:%M:%S'),
        'is_admin': usuario.is_admin
    }
    
    # Adicionar endereço de forma segura
    if usuario.endereco_cep:
        dados_usuario['endereco'] = {
            'cep': usuario.endereco_cep,
            'rua': usuario.endereco_rua,
            'numero': usuario.endereco_numero,
            'complemento': usuario.endereco_complemento,
            'bairro': usuario.endereco_bairro,
            'cidade': usuario.endereco_cidade,
            'estado': usuario.endereco_estado
        }
    
    # CPF mascarado
    if usuario.cpf_hash:
        if hasattr(usuario, 'get_cpf_masked'):
            dados_usuario['cpf'] = usuario.get_cpf_masked()
        else:
            dados_usuario['cpf'] = "***.***.***-**"
    
    # Buscar pedidos do usuário
    pedidos_usuario = []
    pedidos = Pedido.query.filter_by(usuario_id=usuario.id).all()
    
    for pedido in pedidos:
        itens_regulares = []
        for item in ItemPedido.query.filter_by(pedido_id=pedido.id).all():
            produto = Produto.query.get(item.produto_id)
            if produto:
                itens_regulares.append({
                    'produto': produto.nome,
                    'quantidade': item.quantidade,
                    'preco_unitario': float(item.preco_unitario),
                    'subtotal': float(item.preco_unitario * item.quantidade)
                })
        
        itens_personalizados = []
        for item in ItemPedidoPersonalizado.query.filter_by(pedido_id=pedido.id).all():
            bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
            if bolo:
                itens_personalizados.append({
                    'tipo': 'Bolo Personalizado',
                    'nome': bolo.nome,
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
        try:
            recheios = json.loads(bolo.recheios) if bolo.recheios else []
            finalizacao = json.loads(bolo.finalizacao) if bolo.finalizacao else []
        except json.JSONDecodeError:
            recheios = []
            finalizacao = []
        
        bolos_personalizados_usuario.append({
            'id': bolo.id,
            'nome': bolo.nome,
            'massa': bolo.massa,
            'recheios': recheios,
            'cobertura': bolo.cobertura,
            'finalizacao': finalizacao,
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
    
    try:
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
    except Exception as e:
        flash(f'Erro ao exportar dados: {str(e)}', 'danger')
        return redirect(url_for('user.perfil'))