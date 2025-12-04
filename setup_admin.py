from app import create_app
from database import db
from models.models import Usuario
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    admin = Usuario(
        nome='Admin',
        email='rolico@gmail.com',
        senha=generate_password_hash('1234'),
        is_admin=True,
        concordou_politica=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print("Admin criado com sucesso!")
    print(f"Senha: 1234")