from app import create_app
from database import db
from models.models import Usuario
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Verificar se o funcionário já existe
    funcionario_existente = Usuario.query.filter_by(email='funcionario@docesonho.com').first()
    
    if funcionario_existente:
        print("Funcionário já existe!")
        print(f"Email: funcionario@docesonho.com")
    else:
        funcionario = Usuario(
            nome='Funcionário',
            email='funcionario@docesonho.com',
            senha=generate_password_hash('1234'),
            is_funcionario=True,
            is_admin=False,
            concordou_politica=True,
            status='ativo'
        )
        
        db.session.add(funcionario)
        db.session.commit()
        
        print("Funcionário criado com sucesso!")
        print(f"Email: funcionario@docesonho.com")
        print(f"Senha: 1234")