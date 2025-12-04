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
from utils.email_sender import enviar_email  # Supondo que você tenha um módulo para enviar emails
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
        
        cpf = request.form.get('cpf')
        endereco_cep = request.form.get('endereco_cep')
        endereco_rua = request.form.get('endereco_rua')
        endereco_numero = request.form.get('endereco_numero')
        endereco_complemento = request.form.get('endereco_complemento')
        endereco_bairro = request.form.get('endereco_bairro')
        endereco_cidade = request.form.get('endereco_cidade')
        endereco_estado = request.form.get('endereco_estado')
        
        # Criar dicionário com os dados do formulário para reenviar em caso de erro
        dados_formulario = {
            'nome': nome,
            'email': email,
            'cpf': cpf,
            'endereco_cep': endereco_cep,
            'endereco_rua': endereco_rua,
            'endereco_numero': endereco_numero,
            'endereco_complemento': endereco_complemento,
            'endereco_bairro': endereco_bairro,
            'endereco_cidade': endereco_cidade,
            'endereco_estado': endereco_estado
        }
        
        # Validar CPF se fornecido
        if cpf:
            cpf_limpo = cpf.replace('.', '').replace('-', '')
            if not validar_cpf(cpf_limpo):
                flash('CPF inválido. Por favor, verifique os números digitados.', 'danger')
                return render_template('registro.html', dados=dados_formulario)
        
        # Debug
        print(f"Nome: {nome}, Email: {email}, Senha fornecida: {len(senha) if senha else 'Nenhuma'}")
        print(f"Confirmação de senha: {len(confirmar_senha) if confirmar_senha else 'Nenhuma'}")
        print(f"Concordou com política: {concordo_politica}")
        
        # Validações
        if not nome or not email or not senha or not confirmar_senha:
            flash('Todos os campos obrigatórios devem ser preenchidos', 'danger')
            return render_template('registro.html', dados=dados_formulario)
        
        if not concordo_politica:
            flash('Você precisa concordar com a política de privacidade', 'danger')
            return render_template('registro.html', dados=dados_formulario)
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem', 'danger')
            return render_template('registro.html', dados=dados_formulario)
        
        # Verificar requisitos de segurança da senha
        if len(senha) < 8:
            flash('A senha deve ter pelo menos 8 caracteres', 'danger')
            return render_template('registro.html', dados=dados_formulario)
        if not re.search("[a-z]", senha):
            flash('A senha deve conter pelo menos uma letra minúscula', 'danger')
            return render_template('registro.html', dados=dados_formulario)
        if not re.search("[A-Z]", senha):
            flash('A senha deve conter pelo menos uma letra maiúscula', 'danger')
            return render_template('registro.html', dados=dados_formulario)
        if not re.search("[0-9]", senha):
            flash('A senha deve conter pelo menos um número', 'danger')
            return render_template('registro.html', dados=dados_formulario)
        if not re.search("[_@$!%*?&]", senha):
            flash('A senha deve conter pelo menos um caractere especial', 'danger')
            return render_template('registro.html', dados=dados_formulario)
        
        # Verificar se o email já existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este e-mail já está cadastrado', 'danger')
            return render_template('registro.html', dados=dados_formulario)
        
        # Criar novo usuário
        try:
            senha_hash = generate_password_hash(senha)
            
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
            
            # Salvar CPF formatado se fornecido
            if cpf:
                novo_usuario.cpf = cpf  # Salva com a formatação (000.000.000-00)
            
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
            return render_template('registro.html', dados=dados_formulario)
    
    return render_template('registro.html')



@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        lembrar = 'lembrar' in request.form
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verificar se o usuário existe e está bloqueado
        if usuario:
            bloqueado, tempo_restante = usuario.esta_bloqueado()
            
            if bloqueado:
                tempo_formatado = usuario.obter_tempo_bloqueio_formatado()
                flash(f'Muitas tentativas de login falhas. Sua conta está temporariamente bloqueada. Tente novamente em {tempo_formatado}.', 'danger')
                
                # Registrar tentativa de login em conta bloqueada
                try:
                    log = Log(
                        tipo='login_bloqueado',
                        descricao=f'Tentativa de login em conta bloqueada: {email}',
                        usuario_id=usuario.id,
                        ip=request.remote_addr
                    )
                    db.session.add(log)
                    db.session.commit()
                except:
                    pass
                
                return render_template('login.html', email=email)
        
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
            # Registrar tentativa falha
            if usuario:
                usuario.registrar_tentativa_falha()
                
                # Verificar se acabou de ser bloqueado
                bloqueado, tempo_restante = usuario.esta_bloqueado()
                if bloqueado:
                    tempo_formatado = usuario.obter_tempo_bloqueio_formatado()
                    
                    if usuario.tentativas_login == 5:
                        flash(f'Você excedeu o limite de tentativas. Sua conta foi bloqueada por 15 minutos.', 'warning')
                    elif usuario.tentativas_login == 10:
                        flash(f'Você excedeu novamente o limite de tentativas. Sua conta foi bloqueada por 1 hora.', 'warning')
                    elif usuario.tentativas_login >= 15:
                        flash(f'Sua conta foi bloqueada por 24 horas devido a múltiplas tentativas falhas.', 'danger')
                else:
                    flash('Email ou senha incorretos', 'danger')
            else:
                flash('Email ou senha incorretos', 'danger')
            
            # Registrar tentativa de login falha
            try:
                log = Log(
                    tipo='login_falha',
                    descricao=f'Tentativa de login falha para: {email}',
                    usuario_id=usuario.id if usuario else None,
                    ip=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
            except:
                registrar_log(
                    tipo='login_falha',
                    descricao=f'Tentativa de login falha para o email {email}',
                    usuario_id=None
                )
            
            return render_template('login.html', email=email)
        
        # Verificar status da conta
        if hasattr(usuario, 'status') and usuario.status != 'ativo':
            flash('Esta conta está desativada. Entre em contato com o suporte.', 'warning')
            return render_template('login.html')
        
        # Login bem-sucedido - resetar tentativas
        usuario.resetar_tentativas_login()
        
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
        
        # Registrar login bem-sucedido
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
            registrar_log(
                tipo='login',
                descricao=f'Login bem-sucedido para o usuário {usuario.nome}',
                usuario_id=usuario.id
            )
        
        # Salvar na sessão
        session['usuario_id'] = usuario.id
        if token:
            session['auth_token'] = token
        
        # Determinar redirecionamento baseado no tipo de usuário
        if hasattr(usuario, 'is_funcionario') and usuario.is_funcionario:
            proxima_pagina = url_for('funcionario.dashboard')
        else:
            # Admin e usuários comuns vão para a index
            proxima_pagina = url_for('index')
                
        # Configurar cookie de autenticação se "lembrar" estiver marcado
        resposta = redirect(proxima_pagina)
        
        if lembrar and token:
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
        
        # Verificar se o usuário existe
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            # Gerar token único
            token = secrets.token_urlsafe(32)
            
            # Armazenar token no banco de dados com expiração de 1 hora
            usuario.reset_token = token
            usuario.reset_token_expiracao = datetime.now() + timedelta(hours=1)
            
            db.session.commit()
            
            # Criar URL de recuperação
            reset_url = url_for('auth.redefinir_senha', token=token, _external=True)
            
            # Criar mensagem de email
            assunto = "Redefinição de Senha - Doce Sonho Confeitaria"
            mensagem = f"""
            Olá {usuario.nome},
            
            Recebemos uma solicitação para redefinir sua senha. Para continuar, acesse o link abaixo:
            
            {reset_url}
            
            Este link expira em 1 hora.
            
            Se você não solicitou esta redefinição, ignore este email.
            
            Atenciosamente,
            Equipe Doce Sonho Confeitaria
            """
            
            # Criar versão HTML do email
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #d23f72; color: white; padding: 10px 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #fff8fa; }}
                    .button {{ display: inline-block; background-color: #d23f72; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Doce Sonho Confeitaria</h2>
                    </div>
                    <div class="content">
                        <p>Olá <strong>{usuario.nome}</strong>,</p>
                        <p>Recebemos uma solicitação para redefinir sua senha. Para continuar, clique no botão abaixo:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Redefinir minha senha</a>
                        </p>
                        <p>Ou copie e cole este link no seu navegador:</p>
                        <p>{reset_url}</p>
                        <p>Este link expira em <strong>1 hora</strong>.</p>
                        <p>Se você não solicitou esta redefinição, ignore este email.</p>
                    </div>
                    <div class="footer">
                        <p>Atenciosamente,<br>Equipe Doce Sonho Confeitaria</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Enviar email
            enviado = enviar_email(email, assunto, mensagem, html)
            
            if enviado:
                flash('Um link de recuperação foi enviado para o seu email.', 'success')
            else:
                flash('Ocorreu um erro ao enviar o email. Por favor, tente novamente mais tarde.', 'danger')
                
        else:
            # Mesmo se o usuário não existir, mostrar a mesma mensagem por segurança
            flash('Um link de recuperação foi enviado para o seu email, se ele estiver cadastrado.', 'success')
        
        return redirect(url_for('auth.login'))
        
    return render_template('esqueci_senha.html')

@auth_bp.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    # Verificar se o token existe e é válido
    usuario = Usuario.query.filter_by(reset_token=token).first()
    
    # Verificar se o token é válido e não expirou
    if not usuario or usuario.reset_token_expiracao < datetime.now():
        flash('O link de recuperação é inválido ou expirou. Por favor, solicite um novo.', 'danger')
        return redirect(url_for('auth.esqueci_senha'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem. Por favor, tente novamente.', 'danger')
            return render_template('redefinir_senha.html', token=token)
        
        # Validar força da senha
        if len(nova_senha) < 8 or not any(c.isupper() for c in nova_senha) or \
           not any(c.islower() for c in nova_senha) or not any(c.isdigit() for c in nova_senha) or \
           not any(c in '@$!%*?&' for c in nova_senha):
            flash('A senha deve conter pelo menos 8 caracteres, incluindo letras maiúsculas, minúsculas, números e caracteres especiais.', 'danger')
            return render_template('redefinir_senha.html', token=token)
        
        # Atualizar senha (usando a convenção de prefixo que vi no seu código)
        usuario.senha = f"mysql_hash:{hashlib.sha256(nova_senha.encode()).hexdigest()}"
        
        # Limpar token após uso
        usuario.reset_token = None
        usuario.reset_token_expiracao = None
        
        db.session.commit()
        
        flash('Sua senha foi alterada com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('redefinir_senha.html', token=token)

@auth_bp.route('/politica-privacidade')
def politica_privacidade():
    return render_template('politica_privacidade.html')

def validar_cpf(cpf):
    """Valida se o CPF é válido usando o algoritmo oficial"""
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
    if cpf == cpf[0] * 11:
        return False
    
    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    
    resto = (soma * 10) % 11
    if resto == 10 or resto == 11:
        resto = 0
    if resto != int(cpf[9]):
        return False
    
    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    
    resto = (soma * 10) % 11
    if resto == 10 or resto == 11:
        resto = 0
    if resto != int(cpf[10]):
        return False
    
    return True