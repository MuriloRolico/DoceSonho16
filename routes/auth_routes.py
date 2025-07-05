from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models.models import Usuario, Token, Log
from database import db
from datetime import datetime, timedelta
from functools import wraps
import uuid
import jwt
import re
import os
import hashlib
import secrets
from email_sender import enviar_email  # Supondo que você tenha um módulo para enviar emails
from utils.helpers import registrar_log
from flask_mail import Mail, Message

auth_bp = Blueprint('auth', __name__)

# Configuração da extensão Mail
mail = Mail()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verificar se o token está no header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Verificar se o token está nos cookies
        if not token and 'auth_token' in request.cookies:
            token = request.cookies.get('auth_token')
        
        # Verificar se o token está na sessão
        if not token and 'auth_token' in session:
            token = session['auth_token']
            
        if not token:
            flash('Você precisa estar logado para acessar esta página', 'warning')
            return redirect(url_for('auth.login'))
            
        try:
            # Verificar o token
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            usuario = Usuario.query.get(payload['id'])
            
            if not usuario or usuario.status != 'ativo':
                flash('Sessão inválida. Por favor, faça login novamente', 'warning')
                return redirect(url_for('auth.login'))
                
            # Verificar se o token está na lista de tokens válidos
            token_db = Token.query.filter_by(
                usuario_id=usuario.id, 
                token=token,
                is_revogado=False
            ).first()
            
            if not token_db or token_db.data_expiracao < datetime.utcnow():
                flash('Sua sessão expirou. Por favor, faça login novamente', 'warning')
                return redirect(url_for('auth.login'))
                
        except jwt.ExpiredSignatureError:
            flash('Sua sessão expirou. Por favor, faça login novamente', 'warning')
            return redirect(url_for('auth.login'))
        except jwt.InvalidTokenError:
            flash('Sessão inválida. Por favor, faça login novamente', 'warning')
            return redirect(url_for('auth.login'))
        
        # Atualizar último acesso
        usuario.ultimo_acesso = datetime.utcnow()
        db.session.commit()
        
        return f(usuario, *args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verificar se o token está no header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Verificar se o token está nos cookies
        if not token and 'auth_token' in request.cookies:
            token = request.cookies.get('auth_token')
        
        # Verificar se o token está na sessão
        if not token and 'auth_token' in session:
            token = session['auth_token']
            
        if not token:
            flash('Você precisa estar logado como administrador para acessar esta página', 'warning')
            return redirect(url_for('auth.login'))
            
        try:
            # Verificar o token
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            usuario = Usuario.query.get(payload['id'])
            
            if not usuario or usuario.status != 'ativo' or not usuario.is_admin:
                flash('Você não tem permissão para acessar esta página', 'danger')
                return redirect(url_for('index'))
                
            # Verificar se o token está na lista de tokens válidos
            token_db = Token.query.filter_by(
                usuario_id=usuario.id, 
                token=token,
                is_revogado=False
            ).first()
            
            if not token_db or token_db.data_expiracao < datetime.utcnow():
                flash('Sua sessão expirou. Por favor, faça login novamente', 'warning')
                return redirect(url_for('auth.login'))
                
        except jwt.ExpiredSignatureError:
            flash('Sua sessão expirou. Por favor, faça login novamente', 'warning')
            return redirect(url_for('auth.login'))
        except jwt.InvalidTokenError:
            flash('Sessão inválida. Por favor, faça login novamente', 'warning')
            return redirect(url_for('auth.login'))
        
        # Atualizar último acesso
        usuario.ultimo_acesso = datetime.utcnow()
        db.session.commit()
        
        return f(usuario, *args, **kwargs)
    
    return decorated

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        concordo_politica = 'concordo_politica' in request.form or request.form.get('concordo_politica')
        
        # Novos campos
        cpf = request.form.get('cpf')
        endereco_cep = request.form.get('endereco_cep')
        endereco_rua = request.form.get('endereco_rua')
        endereco_numero = request.form.get('endereco_numero')
        endereco_complemento = request.form.get('endereco_complemento')
        endereco_bairro = request.form.get('endereco_bairro')
        endereco_cidade = request.form.get('endereco_cidade')
        endereco_estado = request.form.get('endereco_estado')
        
        # Debug
        print(f"Nome: {nome}, Email: {email}, Senha fornecida: {len(senha) if senha else 'Nenhuma'}")
        print(f"Confirmação de senha: {len(confirmar_senha) if confirmar_senha else 'Nenhuma'}")
        print(f"Concordou com política: {concordo_politica}")
        
        # Validações
        if not nome or not email or not senha or not confirmar_senha:
            flash('Todos os campos obrigatórios devem ser preenchidos', 'danger')
            return render_template('registro.html')
        
        if not concordo_politica:
            flash('Você precisa concordar com a política de privacidade', 'danger')
            return render_template('registro.html')
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem', 'danger')
            return render_template('registro.html')
        
        # Verificar requisitos de segurança da senha
        if len(senha) < 8:
            flash('A senha deve ter pelo menos 8 caracteres', 'danger')
            return render_template('registro.html')
        if not re.search("[a-z]", senha):
            flash('A senha deve conter pelo menos uma letra minúscula', 'danger')
            return render_template('registro.html')
        if not re.search("[A-Z]", senha):
            flash('A senha deve conter pelo menos uma letra maiúscula', 'danger')
            return render_template('registro.html')
        if not re.search("[0-9]", senha):
            flash('A senha deve conter pelo menos um número', 'danger')
            return render_template('registro.html')
        if not re.search("[_@$!%*?&]", senha):
            flash('A senha deve conter pelo menos um caractere especial', 'danger')
            return render_template('registro.html')
        
        # Verificar se o email já existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este e-mail já está cadastrado', 'danger')
            return render_template('registro.html')
        
        # Criar novo usuário
        try:
            senha_hash = generate_password_hash(senha)
            print(f"Hash gerado: {senha_hash}")
            
            novo_usuario = Usuario(
                nome=nome,
                email=email,
                senha=senha_hash,
                concordou_politica=True,
                endereco_cep=endereco_cep,
                endereco_rua=endereco_rua,
                endereco_numero=endereco_numero,
                endereco_complemento=endereco_complemento,
                endereco_bairro=endereco_bairro,
                endereco_cidade=endereco_cidade,
                endereco_estado=endereco_estado,
                status='ativo'
            )
            
            # Criptografar o CPF se fornecido
            if cpf:
                novo_usuario.set_cpf(cpf.replace('.', '').replace('-', ''))
            
            db.session.add(novo_usuario)
            db.session.commit()
            
            # Registrar log usando ambos os métodos
            try:
                log = Log(
                    tipo='registro',
                    descricao=f'Novo usuário registrado: {email}',
                    usuario_id=novo_usuario.id,
                    ip=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
            except:
                # Fallback para registrar_log se Log model não existir
                registrar_log(
                    tipo='registro',
                    descricao=f'Novo usuário registrado: {email}',
                    usuario_id=novo_usuario.id
                )
            
            # Enviar email de boas-vindas
            try:
                enviar_email(
                    destinatario=email,
                    assunto='Bem-vindo à Doce Sonho Confeitaria',
                    mensagem=f'Olá {nome},\n\nSeu cadastro foi realizado com sucesso! Agora você pode fazer pedidos e aproveitar todos os nossos produtos.\n\nAtenciosamente,\nEquipe Doce Sonho Confeitaria'
                )
            except Exception as e:
                # Apenas registrar erro, não impedir o cadastro
                print(f"Erro ao enviar email: {str(e)}")
            
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar usuário: {str(e)}', 'danger')
            print(f"Erro no cadastro: {str(e)}")
            return render_template('registro.html')
    
    return render_template('registro.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        lembrar = 'lembrar' in request.form
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verificar senha com múltiplos formatos
        senha_valida = False
        if usuario:
            # Verifica se a senha está no formato Werkzeug
            if check_password_hash(usuario.senha, senha):
                senha_valida = True
            # Verifica se a senha está no formato mysql_hash
            elif usuario.senha.startswith('mysql_hash:'):
                mysql_hash = usuario.senha.split(':', 1)[1]
                input_hash = hashlib.sha256(senha.encode()).hexdigest()
                if mysql_hash == input_hash:
                    senha_valida = True
        
        if not usuario or not senha_valida:
            # Registrar tentativa de login falha usando ambos os métodos
            try:
                log = Log(
                    tipo='login_falha',
                    descricao=f'Tentativa de login falha para: {email}',
                    ip=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
            except:
                # Fallback para registrar_log
                registrar_log(
                    tipo='login_falha',
                    descricao=f'Tentativa de login falha para o email {email}',
                    usuario_id=None
                )
            
            flash('Email ou senha incorretos', 'danger')
            return render_template('login.html')
        
        if hasattr(usuario, 'status') and usuario.status != 'ativo':
            flash('Esta conta está desativada. Entre em contato com o suporte.', 'warning')
            return render_template('login.html')
        
        # Tentar gerar token JWT (se disponível)
        token = None
        try:
            if hasattr(usuario, 'gerar_auth_token'):
                expira_em = 30 if lembrar else 2  # 30 dias ou 2 horas
                token = usuario.gerar_auth_token(expira_em=expira_em)
                
                # Salvar token no banco se modelo Token existir
                try:
                    novo_token = Token(
                        usuario_id=usuario.id,
                        token=token,
                        device_info=request.user_agent.string,
                        ip=request.remote_addr,
                        data_expiracao=datetime.utcnow() + timedelta(days=expira_em if lembrar else 0, hours=0 if lembrar else expira_em)
                    )
                    db.session.add(novo_token)
                except Exception as e:
                    print(f"Erro ao salvar token: {str(e)}")
        except Exception as e:
            print(f"Erro ao gerar token: {str(e)}")
        
        # Atualizar último acesso
        if hasattr(usuario, 'ultimo_acesso'):
            usuario.ultimo_acesso = datetime.utcnow()
        
        # Registrar login bem-sucedido usando ambos os métodos
        try:
            log = Log(
                tipo='login_sucesso',
                descricao=f'Login bem-sucedido para: {email}',
                usuario_id=usuario.id,
                ip=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        except:
            # Fallback para registrar_log
            registrar_log(
                tipo='login',
                descricao=f'Login bem-sucedido para o usuário {usuario.nome}',
                usuario_id=usuario.id
            )
        
        # Salvar na sessão
        session['usuario_id'] = usuario.id
        if token:
            session['auth_token'] = token
        
        # Configurar cookie de autenticação se "lembrar" estiver marcado
        resposta = redirect(url_for('index'))
        if lembrar and token:
            # Configurar cookie seguro para autenticação
            resposta.set_cookie(
                'auth_token',
                token,
                max_age=30 * 24 * 60 * 60,  # 30 dias
                httponly=True,
                secure=request.is_secure,
                samesite='Lax'
            )
        
        flash('Login realizado com sucesso!', 'success')
        return resposta
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        usuario = Usuario.query.get(usuario_id)
        
        # Revogar token JWT se existir
        if 'auth_token' in session:
            token = session['auth_token']
            try:
                token_db = Token.query.filter_by(token=token).first()
                if token_db:
                    token_db.is_revogado = True
                    db.session.commit()
            except Exception as e:
                print(f"Erro ao revogar token: {str(e)}")
        
        # Registrar log de logout usando ambos os métodos
        try:
            log = Log(
                tipo='logout',
                descricao=f'Logout realizado para: {usuario.email if usuario else "usuário desconhecido"}',
                usuario_id=usuario_id,
                ip=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        except:
            # Fallback para registrar_log
            registrar_log(
                tipo='logout',
                descricao=f'Logout realizado para o usuário {usuario.nome if usuario else "desconhecido"}',
                usuario_id=usuario_id
            )
    
    # Limpar sessão
    session.pop('usuario_id', None)
    session.pop('auth_token', None)
    session.pop('carrinho', None)
    session.pop('carrinho_personalizado', None)
    
    # Limpar cookie
    resposta = redirect(url_for('index'))
    resposta.delete_cookie('auth_token')
    
    flash('Logout realizado com sucesso!', 'success')
    return resposta

@auth_bp.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Por favor, informe seu email', 'danger')
            return redirect(url_for('auth.esqueci_senha'))
        
        # Verificar se o email existe
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            # Gerar token único para redefinição de senha
            token = secrets.token_urlsafe(32)
            expiracao = datetime.utcnow() + timedelta(hours=24)
            
            # Salvar token no banco de dados
            usuario.reset_token = token
            usuario.reset_token_expiracao = expiracao
            
            # Criar um registro na tabela de tokens
            try:
                novo_token = Token(
                    usuario_id=usuario.id,
                    token=token,
                    tipo='reset',
                    device_info=request.user_agent.string,
                    ip=request.remote_addr,
                    data_expiracao=expiracao
                )
                db.session.add(novo_token)
            except Exception as e:
                print(f"Erro ao criar token na tabela: {str(e)}")
            
            db.session.commit()
            
            # Criar link de redefinição
            reset_url = url_for('auth.redefinir_senha', token=token, _external=True)
            
            # Tentar enviar email com Flask-Mail primeiro, depois fallback para email_sender
            email_enviado = False
            
            # Tentativa 1: Flask-Mail
            try:
                msg = Message(
                    'Redefinição de Senha - Doce Sonho Confeitaria',
                    sender=current_app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[email]
                )
                msg.body = f'''Para redefinir sua senha, visite o seguinte link:

{reset_url}

Se você não solicitou a redefinição de senha, ignore este email e nenhuma alteração será feita.

Atenciosamente,
Equipe Doce Sonho Confeitaria
'''
                mail.send(msg)
                email_enviado = True
            except Exception as e:
                print(f"Erro ao enviar email com Flask-Mail: {e}")
                
                # Tentativa 2: email_sender
                try:
                    enviar_email(
                        destinatario=email,
                        assunto='Redefinição de Senha - Doce Sonho Confeitaria',
                        mensagem=f'Olá {usuario.nome},\n\nVocê solicitou a redefinição de sua senha. Clique no link abaixo para criar uma nova senha:\n\n{reset_url}\n\nEste link é válido por 24 horas.\n\nSe você não solicitou esta alteração, ignore este email.\n\nAtenciosamente,\nEquipe Doce Sonho Confeitaria'
                    )
                    email_enviado = True
                except Exception as e2:
                    print(f"Erro ao enviar email com email_sender: {e2}")
            
            if not email_enviado:
                flash('Ocorreu um erro ao enviar o email. Por favor, tente novamente mais tarde.', 'danger')
                return redirect(url_for('auth.esqueci_senha'))
        
        # Por segurança, sempre mostramos a mesma mensagem
        flash('Se o email estiver cadastrado, você receberá instruções para redefinir sua senha.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('esqueci_senha.html')

@auth_bp.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    # Verificar se o token é válido
    usuario = Usuario.query.filter_by(reset_token=token).first()
    
    # Se o token não existir ou estiver expirado
    if not usuario or not usuario.reset_token_expiracao or usuario.reset_token_expiracao < datetime.utcnow():
        flash('O link de redefinição de senha é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.esqueci_senha'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem.', 'danger')
            return render_template('redefinir_senha.html', token=token)
        
        # Verificar requisitos de senha
        if len(nova_senha) < 8:
            flash('A senha deve ter pelo menos 8 caracteres.', 'danger')
            return render_template('redefinir_senha.html', token=token)
        if not re.search("[a-z]", nova_senha):
            flash('A senha deve conter pelo menos uma letra minúscula.', 'danger')
            return render_template('redefinir_senha.html', token=token)
        if not re.search("[A-Z]", nova_senha):
            flash('A senha deve conter pelo menos uma letra maiúscula.', 'danger')
            return render_template('redefinir_senha.html', token=token)
        if not re.search("[0-9]", nova_senha):
            flash('A senha deve conter pelo menos um número.', 'danger')
            return render_template('redefinir_senha.html', token=token)
        if not re.search("[_@$!%*?&]", nova_senha):
            flash('A senha deve conter pelo menos um caractere especial.', 'danger')
            return render_template('redefinir_senha.html', token=token)
        
        # Atualizar a senha
        usuario.senha = generate_password_hash(nova_senha)
        usuario.reset_token = None
        usuario.reset_token_expiracao = None
        
        # Revogar todos os tokens existentes por segurança
        try:
            tokens = Token.query.filter_by(usuario_id=usuario.id, is_revogado=False).all()
            for t in tokens:
                t.is_revogado = True
        except Exception as e:
            print(f"Erro ao revogar tokens: {str(e)}")
        
        db.session.commit()
        
        flash('Sua senha foi redefinida com sucesso! Faça login com sua nova senha.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('redefinir_senha.html', token=token)

@auth_bp.route('/politica-privacidade')
def politica_privacidade():
    return render_template('politica_privacidade.html')