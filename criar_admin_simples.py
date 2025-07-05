#!/usr/bin/env python3
"""
Script para criar usuário administrador no sistema Doce Sonho
Execute este script no diretório raiz do seu projeto Flask
"""

import sys
import os
from werkzeug.security import generate_password_hash

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def criar_admin_simples():
    """Método simples usando apenas geração de hash"""
    senha = input("Digite a senha para o admin (padrão: 1234): ").strip()
    if not senha:
        senha = '1234'
    
    email = input("Digite o email do admin (padrão: Rolico@gmail.com): ").strip()
    if not email:
        email = 'Rolico@gmail.com'
    
    nome = input("Digite o nome do admin (padrão: Admin): ").strip()
    if not nome:
        nome = 'Admin'
    
    # Gerar hash da senha
    senha_hash = generate_password_hash(senha)
    
    # Gerar SQL para inserção
    sql = f"""
-- SQL para criar usuário admin
USE doce_sonho;

-- Remover admin existente (se houver)
DELETE FROM usuario WHERE email = '{email}';

-- Criar novo admin
INSERT INTO usuario (nome, email, senha, is_admin, concordou_politica, status) 
VALUES ('{nome}', '{email}', '{senha_hash}', TRUE, TRUE, 'ativo');

-- Verificar se foi criado
SELECT id, nome, email, is_admin, status FROM usuario WHERE email = '{email}';
"""
    
    # Salvar SQL em arquivo
    with open('criar_admin.sql', 'w', encoding='utf-8') as f:
        f.write(sql)
    
    print("\n" + "="*50)
    print("ADMIN CRIADO COM SUCESSO!")
    print("="*50)
    print(f"Nome: {nome}")
    print(f"Email: {email}")
    print(f"Senha: {senha}")
    print(f"Hash: {senha_hash}")
    print("\nArquivo SQL gerado: criar_admin.sql")
    print("Execute este arquivo no seu MySQL para criar o admin.")
    print("="*50)

def criar_admin_com_flask():
    """Método usando Flask/SQLAlchemy"""
    try:
        # Tentar importar os módulos Flask
        from app import app, db  # Ajuste conforme sua estrutura
        from models import Usuario  # Ajuste conforme sua estrutura
        
        senha = input("Digite a senha para o admin (padrão: 1234): ").strip()
        if not senha:
            senha = '1234'
        
        email = input("Digite o email do admin (padrão: Rolico@gmail.com): ").strip()
        if not email:
            email = 'Rolico@gmail.com'
        
        nome = input("Digite o nome do admin (padrão: Admin): ").strip()
        if not nome:
            nome = 'Admin'
        
        with app.app_context():
            # Verificar se admin já existe
            admin_existente = Usuario.query.filter_by(email=email).first()
            
            if admin_existente:
                print(f"Admin com email {email} já existe. Atualizando...")
                admin_existente.nome = nome
                admin_existente.set_password(senha)
                admin_existente.is_admin = True
                admin_existente.concordou_politica = True
                admin_existente.status = 'ativo'
                admin = admin_existente
            else:
                print("Criando novo admin...")
                admin = Usuario(
                    nome=nome,
                    email=email,
                    is_admin=True,
                    concordou_politica=True,
                    status='ativo'
                )
                admin.set_password(senha)
                db.session.add(admin)
            
            db.session.commit()
            
            print("\n" + "="*50)
            print("ADMIN CRIADO COM SUCESSO!")
            print("="*50)
            print(f"ID: {admin.id}")
            print(f"Nome: {admin.nome}")
            print(f"Email: {admin.email}")
            print(f"Senha: {senha}")
            print(f"Is Admin: {admin.is_admin}")
            print(f"Status: {admin.status}")
            print("="*50)
            
    except ImportError as e:
        print(f"Erro ao importar módulos Flask: {e}")
        print("Usando método alternativo...")
        criar_admin_simples()
    except Exception as e:
        print(f"Erro: {e}")
        print("Usando método alternativo...")
        criar_admin_simples()

def verificar_admin():
    """Verificar se existem admins no sistema"""
    try:
        from app import app, db
        from models import Usuario
        
        with app.app_context():
            admins = Usuario.query.filter_by(is_admin=True).all()
            
            if admins:
                print("\n=== ADMINS ENCONTRADOS ===")
                for admin in admins:
                    print(f"ID: {admin.id} | Nome: {admin.nome} | Email: {admin.email} | Status: {admin.status}")
            else:
                print("\nNenhum admin encontrado no sistema.")
                
    except Exception as e:
        print(f"Erro ao verificar admins: {e}")

def main():
    """Função principal"""
    print("="*50)
    print("CRIADOR DE ADMIN - DOCE SONHO")
    print("="*50)
    print("1. Criar admin usando Flask/SQLAlchemy")
    print("2. Gerar SQL para criar admin")
    print("3. Verificar admins existentes")
    print("4. Sair")
    print("="*50)
    
    while True:
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == '1':
            criar_admin_com_flask()
            break
        elif escolha == '2':
            criar_admin_simples()
            break
        elif escolha == '3':
            verificar_admin()
            break
        elif escolha == '4':
            print("Saindo...")
            break
        else:
            print("Opção inválida! Digite 1, 2, 3 ou 4.")

if __name__ == "__main__":
    main()