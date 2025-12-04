"""
Script de migração para adicionar o campo is_funcionario
Execute este script ANTES de criar o funcionário
"""
from app import create_app
from database import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Adicionar coluna is_funcionario se não existir
        with db.engine.connect() as conn:
            # Verifica se a coluna já existe
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name='usuario' 
                AND column_name='is_funcionario'
            """))
            
            existe = result.scalar()
            
            if existe == 0:
                # Adiciona a coluna
                conn.execute(text("""
                    ALTER TABLE usuario 
                    ADD COLUMN is_funcionario BOOLEAN DEFAULT FALSE
                """))
                conn.commit()
                print("✅ Coluna 'is_funcionario' adicionada com sucesso!")
            else:
                print("ℹ️  Coluna 'is_funcionario' já existe no banco de dados.")
                
    except Exception as e:
        print(f"❌ Erro ao executar migração: {str(e)}")
        db.session.rollback()