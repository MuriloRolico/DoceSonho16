from flask import Flask, render_template, session, g
from database import db
import os
from datetime import timedelta
from routes.auth_routes import auth_bp
from dotenv import load_dotenv


load_dotenv() 

def create_app():
    app = Flask(__name__)
    
    # Configurações de segurança e ambiente
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'doce_sonho_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql://root:root@localhost/doce_sonho')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configurações de upload
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Configurações de segurança adicionais
    app.config['HASH_SALT'] = os.environ.get('HASH_SALT', 'salt-para-hash-sensivel')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    app.config['SESSION_COOKIE_SECURE'] = True  # Requer HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Impede acesso via JavaScript
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Proteção contra CSRF

    # Garantir que os diretórios de upload existem
    os.makedirs(os.path.join(app.root_path, 'static/uploads/profile_pics'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static/uploads/products'), exist_ok=True)

    # Inicializar o banco de dados com a aplicação
    db.init_app(app)

    # Importar modelos APÓS a inicialização do db
    from models.models import Produto, Usuario

    # Importar utilitários APÓS os modelos
    from utils.helpers import is_admin, allowed_file, registrar_log, inicializar_db
    from utils.payment import create_mercadopago_preference

    # Registrar o processador de contexto com funcionalidades expandidas
    @app.context_processor
    def utility_processor():
        def is_admin_context():
            if 'usuario_id' in session:
                usuario = Usuario.query.get(session['usuario_id'])
                return usuario and usuario.is_admin
            return False
        
        def get_usuario():
            if 'usuario_id' in session:
                return Usuario.query.get(session['usuario_id'])
            return None
        
        return {
            'is_admin': is_admin_context,
            'get_usuario': get_usuario
        }

    # Middleware para verificar tokens JWT
    @app.before_request
    def verificar_token():
        if 'auth_token' in session and 'usuario_id' not in session:
            token = session['auth_token']
            usuario = Usuario.verificar_auth_token(token)
            if usuario:
                session['usuario_id'] = usuario.id

    # Importar e registrar rotas - mantendo compatibilidade com estrutura atual
    from routes.auth_routes import auth_bp
    from routes.product_routes import product_bp
    from routes.cart_routes import cart_bp
    from routes.order_routes import order_bp
    from routes.user_routes import user_bp
    from routes.admin_routes import admin_bp
    from routes.sobrenos_routes import sobrenos_bp
   

    
    # Registrar blueprints com prefixos opcionais para nova estrutura
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sobrenos_bp)
    
    
    # Tentar registrar novos blueprints se existirem
    try:
        from auth import auth_bp as new_auth_bp
        from user import user_bp as new_user_bp
        from product import product_bp as new_product_bp
        from order import order_bp as new_order_bp
        from admin import admin_bp as new_admin_bp
        
        
        app.register_blueprint(new_auth_bp, url_prefix='/auth')
        app.register_blueprint(new_user_bp, url_prefix='/user')
        app.register_blueprint(new_product_bp, url_prefix='/product')
        app.register_blueprint(new_order_bp, url_prefix='/order')
        app.register_blueprint(new_admin_bp, url_prefix='/admin')
    except ImportError:
        # Se os novos blueprints não existirem, continua com os antigos
        pass

    # Rota principal
    @app.route('/')
    def index():
        produtos = Produto.query.all()
        return render_template('index.html', produtos=produtos)

    return app

def initialize_database(app):
    """Inicializa o banco de dados com dados padrão"""
    from utils.helpers import inicializar_db
    
    admin_email = 'gerente@docesonho.com'
    admin_senha = 'senha_segura123'
    admin_nome = 'Gerente da Confeitaria'
    
    # Usar o contexto da aplicação para inicializar o banco
    with app.app_context():
        inicializar_db(app, admin_email, admin_senha, admin_nome)

if __name__ == '__main__':
    # Criar a aplicação
    app = create_app()
    
    # Inicializar o banco de dados
    initialize_database(app)
    
    # Executar a aplicação
    app.run(debug=True)