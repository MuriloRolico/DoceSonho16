import os
import re

def find_meus_pedidos_references(search_dir='.'):
    """
    Encontra todas as referências a 'meus_pedidos' em arquivos Python e HTML
    """
    print("🔍 Procurando por todas as referências a 'meus_pedidos'...")
    print("=" * 60)
    
    found_references = []
    
    # Extensões de arquivo para procurar
    extensions = ['.py', '.html', '.htm', '.jinja', '.jinja2']
    
    for root, dirs, files in os.walk(search_dir):
        # Pular diretórios que não precisamos
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'meus_pedidos' in line:
                            found_references.append({
                                'file': file_path,
                                'line': i,
                                'content': line.strip(),
                                'type': 'url_for' if 'url_for' in line else 'other'
                            })
                
                except Exception as e:
                    print(f"❌ Erro ao ler {file_path}: {e}")
    
    return found_references

def analyze_references(references):
    """
    Analisa e categoriza as referências encontradas
    """
    if not references:
        print("✅ Nenhuma referência a 'meus_pedidos' encontrada!")
        return
    
    print(f"📋 Encontradas {len(references)} referências a 'meus_pedidos':")
    print("-" * 60)
    
    url_for_refs = [ref for ref in references if ref['type'] == 'url_for']
    other_refs = [ref for ref in references if ref['type'] == 'other']
    
    if url_for_refs:
        print(f"\n🎯 Referências url_for que precisam ser corrigidas ({len(url_for_refs)}):")
        for ref in url_for_refs:
            print(f"   📁 {ref['file']}:{ref['line']}")
            print(f"      {ref['content']}")
            print()
    
    if other_refs:
        print(f"\n📝 Outras referências encontradas ({len(other_refs)}):")
        for ref in other_refs:
            print(f"   📁 {ref['file']}:{ref['line']}")
            print(f"      {ref['content']}")
            print()

def fix_remaining_meus_pedidos(references):
    """
    Corrige automaticamente as referências restantes
    """
    url_for_refs = [ref for ref in references if ref['type'] == 'url_for']
    
    if not url_for_refs:
        print("✅ Nenhuma referência url_for para corrigir!")
        return
    
    print(f"🔧 Corrigindo {len(url_for_refs)} referências url_for...")
    
    files_to_fix = {}
    for ref in url_for_refs:
        if ref['file'] not in files_to_fix:
            files_to_fix[ref['file']] = []
        files_to_fix[ref['file']].append(ref)
    
    for file_path, refs in files_to_fix.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes = 0
            
            # Substituições específicas para meus_pedidos
            replacements = [
                ("url_for('order.pedidos')", "url_for('order.pedidos')"),
                ('url_for("order.pedidos")', 'url_for("order.pedidos")'),
                ("url_for('order.pedidos',", "url_for('order.pedidos',"),
                ('url_for("order.pedidos",', 'url_for("order.pedidos",'),
                ("url_for('order.pedidos')", "url_for('order.pedidos')"),
                ('url_for("order.pedidos")', 'url_for("order.pedidos")'),
                ("url_for('order.pedidos',", "url_for('order.pedidos',"),
                ('url_for("order.pedidos",', 'url_for("order.pedidos",'),
            ]
            
            for old, new in replacements:
                if old in content:
                    content = content.replace(old, new)
                    changes += content.count(new) - original_content.count(new)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ {file_path} - {changes} alterações")
            
        except Exception as e:
            print(f"   ❌ Erro ao corrigir {file_path}: {e}")

def check_blueprints():
    """
    Verifica se existe definição de rota 'meus_pedidos' nos blueprints
    """
    print("\n🔍 Verificando definições de rotas nos blueprints...")
    
    blueprint_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and any(keyword in file.lower() for keyword in ['order', 'pedido', 'blueprint']):
                blueprint_files.append(os.path.join(root, file))
    
    for file_path in blueprint_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'def meus_pedidos' in content:
                print(f"   📁 Função 'meus_pedidos' encontrada em: {file_path}")
                
                # Procurar pela linha da função
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'def meus_pedidos' in line:
                        print(f"      Linha {i}: {line.strip()}")
        
        except Exception as e:
            continue

if __name__ == '__main__':
    print("🔍 Análise completa de referências 'meus_pedidos'")
    print("=" * 60)
    
    # Encontrar todas as referências
    references = find_meus_pedidos_references()
    
    # Analisar as referências
    analyze_references(references)
    
    # Verificar blueprints
    check_blueprints()
    
    # Corrigir referências restantes
    if references:
        print("\n" + "=" * 60)
        fix_remaining_meus_pedidos(references)
        
        print(f"\n🎯 Resumo final:")
        print(f"   📋 Referências encontradas: {len(references)}")
        print(f"   🔧 Tentativa de correção realizada")
        print(f"   ✅ Execute seu app.py novamente para testar!")
    
    print(f"\n💡 Se o erro persistir, verifique:")
    print(f"   1. Se existe função 'meus_pedidos' em algum blueprint")
    print(f"   2. Se há referências em arquivos JavaScript")
    print(f"   3. Se há referências em templates que incluem outros templates")