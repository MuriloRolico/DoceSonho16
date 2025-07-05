import os
import re

def fix_url_for_references(templates_dir='templates'):
    """
    Script para corrigir automaticamente as referências url_for nos templates
    """
    
    # Endpoints que NÃO devem ser alterados (rotas especiais do Flask)
    SKIP_ENDPOINTS = {'static', 'index'}
    
    # Mapeamento completo de endpoints para blueprints
    endpoint_mappings = {
        # Auth routes
        'login': 'auth.login',
        'register': 'auth.register',
        'registro': 'auth.register',
        'logout': 'auth.logout',
        
        # Product routes
        'todos_produtos': 'product.todos_produtos',
        'produto_detalhes': 'product.produto_detalhes',
        'detalhes_produto': 'product.detalhes_produto',
        'adicionar_produto': 'product.adicionar_produto',
        'editar_produto': 'product.editar_produto',
        'deletar_produto': 'product.deletar_produto',
        'montar_bolo': 'product.montar_bolo',
        'personalizar_bolo': 'product.personalizar_bolo',
        'detalhes_bolo_personalizado': 'product.detalhes_bolo_personalizado',
        'salvar_bolo_personalizado': 'product.salvar_bolo_personalizado',
        'admin_novo_produto': 'product.admin_novo_produto',
        'admin_editar_produto': 'product.admin_editar_produto',
        'admin_deletar_produto': 'product.admin_deletar_produto',
        
        # Cart routes
        'adicionar_ao_carrinho': 'cart.adicionar_ao_carrinho',
        'ver_carrinho': 'cart.carrinho',  # Corrigido: era 'cart.ver_carrinho'
        'carrinho': 'cart.carrinho',
        'remover_do_carrinho': 'cart.remover_do_carrinho',
        'atualizar_carrinho': 'cart.atualizar_carrinho',
        'remover_bolo_personalizado': 'cart.remover_bolo_personalizado',
        'atualizar_bolo_personalizado': 'cart.atualizar_bolo_personalizado',
        
        # Order routes
        'finalizar_pedido': 'order.finalizar_pedido',
        'finalizar_compra': 'order.finalizar_compra',
        'meus_pedidos': 'order.pedidos',  # Corrigido: era 'order.meus_pedidos'
        'pedidos': 'order.pedidos',
        'detalhes_pedido': 'order.detalhes_pedido',
        'cancelar_pedido': 'order.cancelar_pedido',
        'confirmar_pedido': 'order.confirmar_pedido',
        'admin_detalhes_pedido': 'order.detalhes_pedido',
        'admin_atualizar_pedido': 'order.admin_atualizar_pedido',
        
        # User routes
        'perfil': 'user.perfil',
        'editar_perfil': 'user.editar_perfil',
        'dados_pessoais': 'user.dados_pessoais',
        'atualizar_dados': 'user.atualizar_dados',
        'atualizar_perfil': 'user.atualizar_perfil',
        'exportar_dados': 'user.exportar_dados',
        'excluir_conta': 'user.excluir_conta',
        'alterar_senha': 'user.alterar_senha',
        'atualizar_foto': 'user.atualizar_foto',
        
        # Admin routes
        'admin_dashboard': 'admin.admin_dashboard',
        'dashboard': 'admin.dashboard',
        'gerenciar_produtos': 'admin.gerenciar_produtos',
        'gerenciar_usuarios': 'admin.gerenciar_usuarios',
        'relatorios': 'admin.relatorios',
        'logs': 'admin.logs',
        'admin_logs': 'admin.admin_logs',
        'filtrar_logs': 'admin.filtrar_logs',
        'novo_produto': 'admin.novo_produto',
        'admin_pedidos': 'admin.pedidos',
        'admin_produtos': 'admin.produtos',
        'editar_usuario': 'admin.editar_usuario',
        'deletar_usuario': 'admin.deletar_usuario',
        
        # Payment routes
        'pagamento': 'payment.pagamento',
        'processar_pagamento': 'payment.processar_pagamento',
        'callback_pagamento': 'payment.callback_pagamento',
        
        # Outras rotas
        'politica_privacidade': 'main.politica_privacidade',
        'termos_uso': 'main.termos_uso',
        'contato': 'main.contato',
        'sobre': 'main.sobre',
    }
    
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
                    
                    # Substituir cada endpoint
                    for old_endpoint, new_endpoint in endpoint_mappings.items():
                        # Contar quantas vezes o endpoint aparece antes da substituição
                        count_before = content.count(f"url_for('{old_endpoint}')")
                        count_before += content.count(f'url_for("{old_endpoint}")')
                        count_before += content.count(f"url_for('{old_endpoint}',")
                        count_before += content.count(f'url_for("{old_endpoint}",')
                        
                        # Fazer as substituições
                        content = content.replace(f"url_for('{old_endpoint}')", f"url_for('{new_endpoint}')")
                        content = content.replace(f'url_for("{old_endpoint}")', f'url_for("{new_endpoint}")')
                        content = content.replace(f"url_for('{old_endpoint}',", f"url_for('{new_endpoint}',")
                        content = content.replace(f'url_for("{old_endpoint}",', f'url_for("{new_endpoint}",')
                        
                        if count_before > 0:
                            file_changes += count_before
                            print(f"  🔄 {old_endpoint} → {new_endpoint} ({count_before}x)")
                    
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

def check_route_availability():
    """
    Verifica se as rotas estão disponíveis antes de fazer as correções
    """
    print("\n🔍 Verificando disponibilidade das rotas...")
    
    try:
        from flask import current_app
        with current_app.app_context():
            for rule in current_app.url_map.iter_rules():
                if rule.endpoint.startswith('order.'):
                    print(f"   ✅ Rota encontrada: {rule.endpoint}")
    except:
        print("   ⚠️  Não foi possível verificar as rotas (app não está rodando)")
        print("   💡 Execute este script apenas quando o Flask app estiver funcionando")

def find_remaining_issues(templates_dir='templates'):
    """
    Encontra problemas restantes após a correção
    """
    SKIP_ENDPOINTS = {'static', 'index'}
    issues = []
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'url_for(' in line:
                            matches = re.findall(r"url_for\(['\"]([^'\"]*)['\"]", line)
                            for match in matches:
                                if '.' not in match and match not in SKIP_ENDPOINTS:
                                    issues.append({
                                        'file': file_path,
                                        'line': i,
                                        'endpoint': match,
                                        'content': line.strip()
                                    })
                
                except Exception as e:
                    print(f"❌ Erro ao analisar {file_path}: {e}")
    
    return issues

def create_manual_fix_guide(issues):
    """
    Cria um guia para correção manual dos problemas restantes
    """
    if not issues:
        return
    
    print(f"\n📝 Guia para correção manual dos {len(issues)} problemas restantes:")
    print("=" * 60)
    
    # Agrupar por endpoint
    endpoint_count = {}
    for issue in issues:
        endpoint = issue['endpoint']
        if endpoint not in endpoint_count:
            endpoint_count[endpoint] = []
        endpoint_count[endpoint].append(issue)
    
    for endpoint, issue_list in endpoint_count.items():
        print(f"\n🔍 Endpoint: '{endpoint}' ({len(issue_list)} ocorrências)")
        
        # Sugestões baseadas no nome do endpoint
        suggestions = []
        if 'login' in endpoint or 'auth' in endpoint:
            suggestions.append("auth.")
        elif 'produto' in endpoint or 'bolo' in endpoint:
            suggestions.append("product.")
        elif 'carrinho' in endpoint or 'cart' in endpoint:
            suggestions.append("cart.")
        elif 'pedido' in endpoint or 'order' in endpoint:
            suggestions.append("order.")
        elif 'perfil' in endpoint or 'user' in endpoint or 'dados' in endpoint:
            suggestions.append("user.")
        elif 'admin' in endpoint:
            suggestions.append("admin.")
        else:
            suggestions.append("main.")
        
        if suggestions:
            print(f"   💡 Provável blueprint: {suggestions[0]}{endpoint}")
        
        # Mostrar alguns exemplos de arquivos
        for issue in issue_list[:3]:
            print(f"   📁 {issue['file']}:{issue['line']}")
        
        if len(issue_list) > 3:
            print(f"   ... e mais {len(issue_list) - 3} arquivos")

if __name__ == '__main__':
    print("🔧 Corrigindo url_for nos templates...")
    print("=" * 50)
    
    # Verificar rotas disponíveis
    check_route_availability()
    
    # Fazer as correções
    fix_url_for_references()
    
    # Verificar problemas restantes
    remaining_issues = find_remaining_issues()
    
    if remaining_issues:
        create_manual_fix_guide(remaining_issues)
        print(f"\n⚠️  Execute novamente o seu app.py para ver se os erros principais foram resolvidos!")
    else:
        print("\n🎉 Todos os problemas foram corrigidos!")
        print("✅ Agora execute seu app.py - os erros de url_for devem estar resolvidos!")
    
    print(f"\n🎯 Correção específica aplicada:")
    print(f"   'meus_pedidos' agora aponta para 'order.pedidos'")
    print(f"   (baseado no erro: Could not build url for endpoint 'order.meus_pedidos')")