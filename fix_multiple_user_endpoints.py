import os
import re

def fix_multiple_user_endpoints():
    """
    Corrige múltiplos endpoints de usuário de uma vez
    """
    
    # Mapeamento de correções para endpoints de usuário
    user_endpoint_fixes = {
        'user.encerrar_todas_sessoes': 'auth.logout',
        'user.atualizar_privacidade': 'user.atualizar_perfil',
        'user.privacidade': 'user.atualizar_perfil',
        'encerrar_todas_sessoes': 'auth.logout',
        'atualizar_privacidade': 'user.atualizar_perfil',
        'privacidade': 'user.atualizar_perfil',
    }
    
    files_modified = 0
    changes_made = 0
    
    print("🔧 Corrigindo múltiplos endpoints de usuário...")
    print("=" * 60)
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
        
        for file in files:
            if file.endswith(('.html', '.py')):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    file_changes = 0
                    
                    # Aplicar todas as correções
                    for old_endpoint, new_endpoint in user_endpoint_fixes.items():
                        # Variações com aspas simples
                        old_pattern = f"url_for('{old_endpoint}')"
                        new_pattern = f"url_for('{new_endpoint}')"
                        count = content.count(old_pattern)
                        if count > 0:
                            content = content.replace(old_pattern, new_pattern)
                            file_changes += count
                            print(f"  🔄 {old_pattern} → {new_pattern} ({count}x)")
                        
                        # Variações com aspas duplas
                        old_pattern = f'url_for("{old_endpoint}")'
                        new_pattern = f'url_for("{new_endpoint}")'
                        count = content.count(old_pattern)
                        if count > 0:
                            content = content.replace(old_pattern, new_pattern)
                            file_changes += count
                            print(f"  🔄 {old_pattern} → {new_pattern} ({count}x)")
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"✅ {file_path} - {file_changes} alterações")
                        files_modified += 1
                        changes_made += file_changes
                
                except Exception as e:
                    continue
    
    print(f"\n📊 Resumo final:")
    print(f"   📁 Arquivos modificados: {files_modified}")
    print(f"   🔄 Total de alterações: {changes_made}")

if __name__ == '__main__':
    fix_multiple_user_endpoints()
