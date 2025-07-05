import os
import re

def fix_encerrar_todas_sessoes_references(templates_dir='templates'):
    """
    Corrige especificamente as referências user.encerrar_todas_sessoes
    """
    print("🔧 Corrigindo referências user.encerrar_todas_sessoes...")
    print("=" * 60)
    
    files_modified = 0
    changes_made = 0
    
    # Procurar por todos os arquivos HTML nos templates
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    file_changes = 0
                    
                    # Substituições específicas para user.encerrar_todas_sessoes
                    replacements = [
                        # Opção 1: Redirecionar para logout (mais comum)
                        ("url_for('auth.logout')", "url_for('auth.logout')"),
                        ('url_for("auth.logout")', 'url_for("auth.logout")'),
                        
                        # Opção 2: Se houver parâmetros, manter os parâmetros
                        ("url_for('user.encerrar_todas_sessoes',", "url_for('auth.logout',"),
                        ('url_for("user.encerrar_todas_sessoes",', 'url_for("auth.logout",'),
                        
                        # Opção 3: Se alguém usar apenas 'encerrar_todas_sessoes'
                        ("url_for('encerrar_todas_sessoes')", "url_for('auth.logout')"),
                        ('url_for("encerrar_todas_sessoes")', 'url_for("auth.logout")'),
                    ]
                    
                    for old, new in replacements:
                        count_before = content.count(old)
                        if count_before > 0:
                            content = content.replace(old, new)
                            file_changes += count_before
                            print(f"  🔄 {old} → {new} ({count_before}x)")
                    
                    # Se houve mudanças, salvar o arquivo
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"✅ {file_path} - {file_changes} alterações")
                        files_modified += 1
                        changes_made += file_changes
                    
                except Exception as e:
                    print(f"❌ Erro ao processar {file_path}: {e}")
    
    # Verificar também arquivos Python
    for root, dirs, files in os.walk('.'):
        # Pular diretórios desnecessários
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    file_changes = 0
                    
                    # Verificar redirecionamentos em Python
                    python_replacements = [
                        ("redirect(url_for('auth.logout'))", "redirect(url_for('auth.logout'))"),
                        ('redirect(url_for("auth.logout"))', 'redirect(url_for("auth.logout"))'),
                        ("return redirect(url_for('auth.logout'))", "return redirect(url_for('auth.logout'))"),
                        ('return redirect(url_for("auth.logout"))', 'return redirect(url_for("auth.logout"))'),
                        ("url_for('auth.logout')", "url_for('auth.logout')"),
                        ('url_for("auth.logout")', 'url_for("auth.logout")'),
                    ]
                    
                    for old, new in python_replacements:
                        count_before = content.count(old)
                        if count_before > 0:
                            content = content.replace(old, new)
                            file_changes += count_before
                            print(f"  🔄 {old} → {new} ({count_before}x)")
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"✅ {file_path} - {file_changes} alterações")
                        files_modified += 1
                        changes_made += file_changes
                    
                except Exception as e:
                    continue  # Ignorar erros em arquivos Python
    
    print(f"\n📊 Resumo:")
    print(f"   📁 Arquivos modificados: {files_modified}")
    print(f"   🔄 Total de alterações: {changes_made}")
    
    if changes_made > 0:
        print(f"\n🎯 Correções aplicadas:")
        print(f"   'user.encerrar_todas_sessoes' → 'auth.logout'")
        print(f"   'encerrar_todas_sessoes' → 'auth.logout'")
        print(f"\n💡 Razão: O endpoint 'user.encerrar_todas_sessoes' não existe.")
        print(f"   Redirecionando para 'auth.logout' que é o endpoint correto para sair.")
    else:
        print(f"\n⚠️  Nenhuma referência encontrada.")

def find_all_encerrar_sessoes_references():
    """
    Encontra todas as referências a user.encerrar_todas_sessoes
    """
    print(f"\n🔍 Procurando todas as referências a encerrar_todas_sessoes...")
    
    references = []
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
        
        for file in files:
            if file.endswith(('.html', '.py', '.js')):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'encerrar_todas_sessoes' in line and 'url_for' in line:
                            references.append({
                                'file': file_path,
                                'line': i,
                                'content': line.strip()
                            })
                
                except Exception as e:
                    continue
    
    if references:
        print(f"📋 Encontradas {len(references)} referências:")
        for ref in references:
            print(f"   📁 {ref['file']}:{ref['line']}")
            print(f"      {ref['content']}")
    else:
        print("✅ Nenhuma referência problemática encontrada!")

def create_alternative_solutions():
    """
    Sugere soluções alternativas se você quiser implementar a funcionalidade
    """
    print(f"\n💡 SOLUÇÕES ALTERNATIVAS:")
    print("=" * 50)
    
    print("1️⃣ CORREÇÃO SIMPLES (Recomendada):")
    print("   user.encerrar_todas_sessoes → auth.logout")
    print("   Motivo: Usar o endpoint de logout existente")
    
    print("\n2️⃣ IMPLEMENTAR A FUNCIONALIDADE:")
    print("   Se você realmente precisa de 'encerrar_todas_sessoes',")
    print("   adicione esta rota no seu arquivo user.py:")
    
    route_code = '''
@user_bp.route('/encerrar-todas-sessoes', methods=['POST'])
@login_required
def encerrar_todas_sessoes():
    """
    Encerra todas as sessões do usuário atual
    """
    try:
        # Limpar dados da sessão
        session.clear()
        
        # Fazer logout
        logout_user()
        
        flash('Todas as sessões foram encerradas com sucesso.', 'success')
        return redirect(url_for('auth.login'))
    
    except Exception as e:
        flash('Erro ao encerrar sessões.', 'error')
        return redirect(url_for('user.perfil'))
'''
    
    print(route_code)
    
    print("\n3️⃣ OUTRAS OPÇÕES:")
    print("   • user.encerrar_todas_sessoes → user.perfil")
    print("   • user.encerrar_todas_sessoes → user.dados_pessoais")
    print("   • user.encerrar_todas_sessoes → main.index")

def update_final_mappings():
    """
    Atualiza o mapeamento final com a nova correção
    """
    print(f"\n📝 Atualizando mapeamento final...")
    
    # Mapeamento atualizado com a nova correção
    updated_mappings = {
        # Auth routes
        'login': 'auth.login',
        'register': 'auth.registro',
        'registro': 'auth.registro',
        'logout': 'auth.logout',
        'politica_privacidade': 'auth.politica_privacidade',
        'termos_uso': 'auth.termos_uso',
        
        # User routes (CORRIGIDO)
        'perfil': 'user.perfil',
        'editar_perfil': 'user.editar_perfil',
        'dados_pessoais': 'user.dados_pessoais',
        'atualizar_dados': 'user.atualizar_dados',
        'atualizar_perfil': 'user.atualizar_perfil',
        'exportar_dados': 'user.exportar_dados',
        'excluir_conta': 'user.excluir_conta',
        'alterar_senha': 'user.alterar_senha',
        'atualizar_foto': 'user.atualizar_foto',
        'encerrar_todas_sessoes': 'auth.logout',  # NOVO: Correção adicionada
        
        # Product routes
        'todos_produtos': 'product.todos_produtos',
        'produto_detalhes': 'product.produto_detalhes',
        # ... (resto permanece igual)
    }
    
    print("✅ Mapeamento atualizado!")
    print("   🆕 encerrar_todas_sessoes → auth.logout")
    
    return updated_mappings

if __name__ == '__main__':
    print("🔧 Correção específica para user.encerrar_todas_sessoes")
    print("=" * 60)
    
    # Procurar todas as referências primeiro
    find_all_encerrar_sessoes_references()
    
    # Fazer as correções
    fix_encerrar_todas_sessoes_references()
    
    # Mostrar soluções alternativas
    create_alternative_solutions()
    
    # Atualizar mapeamentos finais
    update_final_mappings()
    
    print(f"\n✅ Execute seu app.py novamente para verificar se o erro foi resolvido!")
    print(f"🎯 Se você precisar da funcionalidade real, implemente a rota sugerida.")
    print(f"📝 Caso contrário, o redirecionamento para 'auth.logout' deve funcionar.")