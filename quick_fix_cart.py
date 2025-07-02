import os
import re

def fix_cart_references(templates_dir='templates'):
    """
    Corrige especificamente as referências cart.ver_carrinho para cart.carrinho
    """
    print("🔧 Corrigindo referências cart.ver_carrinho...")
    print("=" * 50)
    
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
                    
                    # Substituições específicas para cart
                    replacements = [
                        ("url_for('cart.ver_carrinho')", "url_for('cart.carrinho')"),
                        ('url_for("cart.ver_carrinho")', 'url_for("cart.carrinho")'),
                        ("url_for('cart.ver_carrinho',", "url_for('cart.carrinho',"),
                        ('url_for("cart.ver_carrinho",', 'url_for("cart.carrinho",'),
                        ("url_for('cart.carrinho')", "url_for('cart.carrinho')"),
                        ('url_for("cart.carrinho")', 'url_for("cart.carrinho")'),
                        ("url_for('ver_carrinho',", "url_for('cart.carrinho',"),
                        ('url_for("ver_carrinho",', 'url_for("cart.carrinho",'),
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
                        ("redirect(url_for('cart.carrinho'))", "redirect(url_for('cart.carrinho'))"),
                        ('redirect(url_for("cart.carrinho"))', 'redirect(url_for("cart.carrinho"))'),
                        ("return redirect(url_for('cart.carrinho'))", "return redirect(url_for('cart.carrinho'))"),
                        ('return redirect(url_for("cart.carrinho"))', 'return redirect(url_for("cart.carrinho"))'),
                        ("url_for('cart.carrinho')", "url_for('cart.carrinho')"),
                        ('url_for("cart.carrinho")', 'url_for("cart.carrinho")'),
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
        print(f"   'ver_carrinho' → 'cart.carrinho'")
        print(f"   'cart.ver_carrinho' → 'cart.carrinho'")
    else:
        print(f"\n⚠️  Nenhuma referência encontrada nos templates.")
        print(f"   O problema pode estar em:")
        print(f"   1. Arquivos JavaScript")
        print(f"   2. Templates com nomes diferentes")
        print(f"   3. Código Python que não foi verificado")

def find_all_cart_references():
    """
    Encontra todas as referências a carrinho/ver_carrinho
    """
    print(f"\n🔍 Procurando todas as referências a carrinho...")
    
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
                        if ('ver_carrinho' in line or 'cart.carrinho' in line) and 'url_for' in line:
                            references.append({
                                'file': file_path,
                                'line': i,
                                'content': line.strip()
                            })
                
                except Exception as e:
                    continue
    
    if references:
        print(f"📋 Encontradas {len(references)} referências:")
        for ref in references[:10]:  # Mostrar apenas as primeiras 10
            print(f"   📁 {ref['file']}:{ref['line']}")
            print(f"      {ref['content']}")
        
        if len(references) > 10:
            print(f"   ... e mais {len(references) - 10} referências")
    else:
        print("✅ Nenhuma referência problemática encontrada!")

if __name__ == '__main__':
    print("🔧 Correção específica para cart.ver_carrinho")
    print("=" * 50)
    
    # Fazer as correções
    fix_cart_references()
    
    # Mostrar referências restantes
    find_all_cart_references()
    
    print(f"\n✅ Execute seu app.py novamente para verificar se o erro foi resolvido!")