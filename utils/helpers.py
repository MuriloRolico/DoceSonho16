from flask import session, request
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import os
from database import db
from functools import wraps
from flask import session, redirect, url_for, flash
from models.models import Usuario

def allowed_file(filename):
    from flask import current_app
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_admin():
    if 'usuario_id' in session:
        # Import dentro da função para evitar importação circular
        from models.models import Usuario
        usuario = Usuario.query.get(session['usuario_id'])
        return usuario and usuario.is_admin
    return False





def funcionario_bloqueado(f):
    """
    Decorator para bloquear acesso de funcionários a rotas de clientes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' in session:
            usuario = Usuario.query.get(session['usuario_id'])
            if usuario and usuario.is_funcionario:
                flash('Funcionários não têm acesso a esta área.', 'warning')
                return redirect(url_for('funcionario.dashboard'))
        return f(*args, **kwargs)
    return decorated_function









def registrar_log(tipo, descricao, usuario_id=None):
    """
    Registra um log no sistema
    
    Args:
        tipo: Tipo do log (ex: 'login', 'produto_novo', 'pedido_atualizado')
        descricao: Descrição detalhada da ação
        usuario_id: ID do usuário que realizou a ação (opcional)
    """
    try:
        # Import dentro da função para evitar importação circular
        from models.models import Log
        
        # Criar log SEM campo IP
        novo_log = Log(
            tipo=tipo,
            descricao=descricao,
            usuario_id=usuario_id,
            data=datetime.now()
        )
        
        db.session.add(novo_log)
        db.session.commit()
        
        print(f"✅ Log registrado: [{tipo}] {descricao[:50]}...")
        
    except Exception as e:
        print(f"❌ Erro ao registrar log: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

def inicializar_db(app, admin_email='admin@docesonho.com', admin_senha='admin123', admin_nome='Administrador'):
    # Import dentro da função para evitar importação circular
    from models.models import Usuario, Produto
    
    with app.app_context():
        db.create_all()
        
        # Verificar se já existe um admin
        admin = Usuario.query.filter_by(is_admin=True).first()
        if not admin:
            # Criar um admin com os dados fornecidos
            admin = Usuario(
                nome=admin_nome,
                email=admin_email,
                senha=generate_password_hash(admin_senha),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f'Administrador {admin_email} criado com sucesso!')
        
        # Verificar se já existem produtos
        if Produto.query.count() == 0:
            produtos = [
                Produto(
                    nome='Bolo de Chocolate', 
                    descricao='Delicioso bolo de chocolate com cobertura de ganache', 
                    preco=45.90, 
                    categoria='Bolos',
                    peso=1.2,
                    ingredientes='Farinha de trigo, açúcar, ovos, chocolate, leite, manteiga',
                    data_validade=datetime.now() + timedelta(days=5),
                    informacoes_nutricionais='Porção de 100g: Calorias: 450, Carboidratos: 55g, Proteínas: 6g, Gorduras: 25g'
                ),
                Produto(
                    nome='Bolo de Morango', 
                    descricao='Bolo de baunilha com recheio de morango', 
                    preco=48.90, 
                    categoria='Bolos',
                    peso=1.0,
                    ingredientes='Farinha de trigo, açúcar, ovos, morango, leite, baunilha',
                    data_validade=datetime.now() + timedelta(days=4),
                    informacoes_nutricionais='Porção de 100g: Calorias: 400, Carboidratos: 50g, Proteínas: 5g, Gorduras: 20g'
                ),
            ]
            
            for produto in produtos:
                db.session.add(produto)
            
            db.session.commit()
            print('Banco de dados inicializado com sucesso!')