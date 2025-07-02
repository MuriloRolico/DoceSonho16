from flask import Flask, render_template
from database import db
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'doce_sonho_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/doce_sonho'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Garantir que o diretório de upload existe
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Inicializar o banco de dados com a aplicação
    db.init_app(app)

    # Importar modelos APÓS a inicialização do db
    from models.models import Produto

    # Importar utilitários APÓS os modelos
    from utils.helpers import is_admin, allowed_file, registrar_log, inicializar_db
    from utils.payment import create_mercadopago_preference

    # Registrar o processador de contexto
    @app.context_processor
    def utility_processor():
        return {
            'is_admin': is_admin
        }

    # Importar e registrar rotas
    from routes.auth_routes import auth_bp
    from routes.product_routes import product_bp
    from routes.cart_routes import cart_bp
    from routes.order_routes import order_bp
    from routes.user_routes import user_bp
    from routes.admin_routes import admin_bp
    from routes.sobrenos_routes import sobrenos_bp
    

    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sobrenos_bp)

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