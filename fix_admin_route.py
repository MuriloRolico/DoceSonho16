import os
import re

def fix_admin_route_references():
    """
    Corrige referências de rotas admin que estão no blueprint errado
    """
    print("🔧 Corrigindo referências de rotas admin...")
    print("=" * 50)
    
    files_modified = 0
    changes_made = 0
    
    # Mapeamento de correções baseado nos erros encontrados
    admin_route_corrections = {
        # Rotas que estão sendo chamadas como product.admin_* mas são admin.admin_*
        "url_for('admin.admin_novo_produto')": "url_for('admin.admin_novo_produto')",
        'url_for("admin.admin_novo_produto")': 'url_for("admin.admin_novo_produto")',
        "url_for('admin.admin_novo_produto',": "url_for('admin.admin_novo_produto',",
        'url_for("admin.admin_novo_produto",': 'url_for("admin.admin_novo_produto",',
        
        "url_for('admin.admin_editar_produto')": "url_for('admin.admin_editar_produto')",
        'url_for("admin.admin_editar_produto")': 'url_for("admin.admin_editar_produto")',
        "url_for('admin.admin_editar_produto',": "url_for('admin.admin_editar_produto',",
        'url_for("admin.admin_editar_produto",': 'url_for("admin.admin_editar_produto",',
        
        "url_for('admin.admin_deletar_produto')": "url_for('admin.admin_deletar_produto')",
        'url_for("admin.admin_deletar_produto")': 'url_for("admin.admin_deletar_produto")',
        "url_for('admin.admin_deletar_produto',": "url_for('admin.admin_deletar_produto',",
        'url_for("admin.admin_deletar_produto",': 'url_for("admin.admin_deletar_produto",',
        
        # Outras possíveis rotas admin que podem estar no blueprint errado
        "url_for('admin.admin_detalhes_pedido')": "url_for('admin.admin_detalhes_pedido')",
        'url_for("admin.admin_detalhes_pedido")': 'url_for("admin.admin_detalhes_pedido")',
        "url_for('admin.admin_atualizar_pedido')": "url_for('admin.admin_atualizar_pedido')",
        'url_for("admin.admin_atualizar_pedido")': 'url_for("admin.admin_atualizar_pedido")',
        
        # Rotas que podem estar sendo chamadas incorretamente
        "url_for('admin.admin_novo_produto')": "url_for('admin.admin_novo_produto')",
        'url_for("admin.admin_novo_produto")': 'url_for("admin.admin_novo_produto")',
    }
    
    # Procurar em todos os arquivos
    for root, dirs, files in os.walk('.'):
        # Pular diretórios desnecessários
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
        
        for file in files:
            if file.endswith(('.html', '.py')):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    file_changes = 0
                    
                    # Aplicar correções
                    for old, new in admin_route_corrections.items():
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
    
    print(f"\n📊 Resumo:")
    print(f"   📁 Arquivos modificados: {files_modified}")
    print(f"   🔄 Total de alterações: {changes_made}")
    
    if changes_made > 0:
        print(f"\n🎯 Correções aplicadas:")
        print(f"   'product.admin_*' → 'admin.admin_*'")
        print(f"   'order.admin_*' → 'admin.admin_*'")
        print(f"   'novo_produto' → 'admin.admin_novo_produto'")
    else:
        print(f"\n⚠️  Nenhuma referência encontrada.")

def find_misplaced_admin_routes():
    """
    Encontra todas as referências a rotas admin que podem estar no blueprint errado
    """
    print(f"\n🔍 Procurando rotas admin mal referenciadas...")
    
    references = []
    patterns = [
        'product.admin_',
        'order.admin_',
        'user.admin_',
        'cart.admin_',
        'payment.admin_'
    ]
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
        
        for file in files:
            if file.endswith(('.html', '.py')):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        for pattern in patterns:
                            if pattern in line and 'url_for' in line:
                                references.append({
                                    'file': file_path,
                                    'line': i,
                                    'content': line.strip(),
                                    'pattern': pattern
                                })
                
                except Exception as e:
                    continue
    
    if references:
        print(f"📋 Encontradas {len(references)} referências suspeitas:")
        for ref in references[:15]:  # Mostrar as primeiras 15
            print(f"   📁 {ref['file']}:{ref['line']}")
            print(f"      {ref['content']}")
            print(f"      🎯 Padrão: {ref['pattern']}")
            print()
        
        if len(references) > 15:
            print(f"   ... e mais {len(references) - 15} referências")
    else:
        print("✅ Nenhuma referência suspeita encontrada!")

def create_blueprint_analysis():
    """
    Analisa como os blueprints estão organizados
    """
    print(f"\n📋 Analisando organização dos blueprints...")
    
    blueprint_routes = {
        'admin': [],
        'product': [],
        'order': [],
        'user': [],
        'cart': [],
        'auth': [],
        'main': [],
        'payment': []
    }
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py') and ('blueprint' in file or 'routes' in file or file in ['admin.py', 'product.py', 'auth.py', 'main.py']):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Procurar definições de rotas
                    route_pattern = r'@\w+\.route\([\'"]([^\'"]+)[\'"].*?\)\s*def\s+(\w+)'
                    matches = re.findall(route_pattern, content, re.MULTILINE | re.DOTALL)
                    
                    # Determinar blueprint baseado no nome do arquivo
                    blueprint_name = 'unknown'
                    if 'admin' in file:
                        blueprint_name = 'admin'
                    elif 'product' in file:
                        blueprint_name = 'product'
                    elif 'auth' in file:
                        blueprint_name = 'auth'
                    elif 'order' in file:
                        blueprint_name = 'order'
                    elif 'user' in file:
                        blueprint_name = 'user'
                    elif 'cart' in file:
                        blueprint_name = 'cart'
                    elif 'main' in file:
                        blueprint_name = 'main'
                    elif 'payment' in file:
                        blueprint_name = 'payment'
                    
                    for route, function in matches:
                        if blueprint_name in blueprint_routes:
                            blueprint_routes[blueprint_name].append({
                                'route': route,
                                'function': function,
                                'file': file_path,
                                'endpoint': f'{blueprint_name}.{function}'
                            })
                
                except Exception as e:
                    continue
    
    print("📊 Rotas encontradas por blueprint:")
    for blueprint, routes in blueprint_routes.items():
        if routes:
            print(f"\n🔹 {blueprint.upper()} ({len(routes)} rotas):")
            for route in routes[:5]:  # Mostrar apenas as primeiras 5
                print(f"   {route['route']} → {route['endpoint']}")
            if len(routes) > 5:
                print(f"   ... e mais {len(routes) - 5} rotas")

if __name__ == '__main__':
    print("🔧 Correção de rotas admin mal referenciadas")
    print("=" * 60)
    
    # Analisar organização atual
    create_blueprint_analysis()
    
    # Procurar referências problemáticas
    find_misplaced_admin_routes()
    
    # Fazer as correções
    fix_admin_route_references()
    
    print(f"\n✅ Execute seu app.py novamente para verificar se o erro foi resolvido!")
    print(f"🎯 Padrão identificado: Todas as rotas admin estão no blueprint 'admin'")
    print(f"   - product.admin_* → admin.admin_*")
    print(f"   - order.admin_* → admin.admin_*")
    print(f"   - etc.")