from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import re
from database import db
from models.models import Usuario
from utils.helpers import registrar_log

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            # Verifica se a senha está no formato Werkzeug
            if check_password_hash(usuario.senha, senha):
                session['usuario_id'] = usuario.id
                
                # Registrar log de login
                registrar_log(
                    tipo='login',
                    descricao=f'Login bem-sucedido para o usuário {usuario.nome}',
                    usuario_id=usuario.id
                )
                
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
            # Verifica se a senha está no formato mysql_hash
            elif usuario.senha.startswith('mysql_hash:'):
                mysql_hash = usuario.senha.split(':', 1)[1]
                import hashlib
                input_hash = hashlib.sha256(senha.encode()).hexdigest()
                if mysql_hash == input_hash:
                    session['usuario_id'] = usuario.id
                    
                    # Registrar log de login
                    registrar_log(
                        tipo='login',
                        descricao=f'Login bem-sucedido para o usuário {usuario.nome} (formato mysql_hash)',
                        usuario_id=usuario.id
                    )
                    
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(url_for('index'))
                
        # Registrar tentativa de login falha
        registrar_log(
            tipo='login_falha',
            descricao=f'Tentativa de login falha para o email {email}',
            usuario_id=None
        )
        
        flash('Email ou senha incorretos!', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        usuario = Usuario.query.get(usuario_id)
        
        # Registrar log de logout
        registrar_log(
            tipo='logout',
            descricao=f'Logout realizado para o usuário {usuario.nome if usuario else "desconhecido"}',
            usuario_id=usuario_id
        )
    
    session.pop('usuario_id', None)
    session.pop('carrinho', None)
    session.pop('carrinho_personalizado', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        concordo_politica = request.form.get('concordo_politica')
        
        # Debug
        print(f"Nome: {nome}, Email: {email}, Senha fornecida: {len(senha) if senha else 'Nenhuma'}")
        print(f"Confirmação de senha: {len(confirmar_senha) if confirmar_senha else 'Nenhuma'}")
        print(f"Concordou com política: {concordo_politica}")
        
        # Verificar se a política de privacidade foi aceita
        if not concordo_politica:
            flash('Você precisa concordar com a Política de Privacidade para se cadastrar', 'danger')
            return render_template('registro.html')
        
        # Verificar se as senhas coincidem
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
        
        usuario_existente = Usuario.query.filter_by(email=email).first()
        
        if usuario_existente:
            flash('Email já cadastrado!', 'danger')
        else:
            try:
                senha_hash = generate_password_hash(senha)
                print(f"Hash gerado: {senha_hash}")
                
                novo_usuario = Usuario(
                    nome=nome,
                    email=email,
                    senha=senha_hash,
                    concordou_politica=True
                )
                
                db.session.add(novo_usuario)
                db.session.commit()
                
                flash('Cadastro realizado com sucesso!', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar: {str(e)}', 'danger')
                print(f"Erro no cadastro: {str(e)}")
    
    return render_template('registro.html')

@auth_bp.route('/politica-privacidade')
def politica_privacidade():
    return render_template('politica_privacidade.html')