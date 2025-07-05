import os
import re

def fix_politica_privacidade_references(templates_dir='templates'):
    """
    Corrige especificamente as referências politica_privacidade para auth.politica_privacidade
    """
    print("🔧 Corrigindo referências politica_privacidade...")
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
                    
                    # Substituições específicas para politica_privacidade
                    replacements = [
                        ("url_for('auth.politica_privacidade')", "url_for('auth.politica_privacidade')"),
                        ('url_for("auth.politica_privacidade")', 'url_for("auth.politica_privacidade")'),
                        ("url_for('politica_privacidade',", "url_for('auth.politica_privacidade',"),
                        ('url_for("politica_privacidade",', 'url_for("auth.politica_privacidade",'),
                        ("url_for('auth.politica_privacidade')", "url_for('auth.politica_privacidade')"),
                        ('url_for("auth.politica_privacidade")', 'url_for("auth.politica_privacidade")'),
                        ("url_for('main.politica_privacidade',", "url_for('auth.politica_privacidade',"),
                        ('url_for("main.politica_privacidade",', 'url_for("auth.politica_privacidade",'),
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
                        ("redirect(url_for('auth.politica_privacidade'))", "redirect(url_for('auth.politica_privacidade'))"),
                        ('redirect(url_for("auth.politica_privacidade"))', 'redirect(url_for("auth.politica_privacidade"))'),
                        ("return redirect(url_for('auth.politica_privacidade'))", "return redirect(url_for('auth.politica_privacidade'))"),
                        ('return redirect(url_for("auth.politica_privacidade"))', 'return redirect(url_for("auth.politica_privacidade"))'),
                        ("url_for('auth.politica_privacidade')", "url_for('auth.politica_privacidade')"),
                        ('url_for("auth.politica_privacidade")', 'url_for("auth.politica_privacidade")'),
                        ("url_for('auth.politica_privacidade')", "url_for('auth.politica_privacidade')"),
                        ('url_for("auth.politica_privacidade")', 'url_for("auth.politica_privacidade")'),
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
        print(f"   'politica_privacidade' → 'auth.politica_privacidade'")
        print(f"   'main.politica_privacidade' → 'auth.politica_privacidade'")
    else:
        print(f"\n⚠️  Nenhuma referência encontrada nos templates.")

def update_main_script_mapping():
    """
    Atualiza o mapeamento no script principal para corrigir blueprints incorretos
    """
    print(f"\n🔧 Criando mapeamento atualizado...")
    
    corrected_mappings = {
        # Auth routes (corrected)
        'login': 'auth.login',
        'register': 'auth.register',
        'registro': 'auth.register',
        'logout': 'auth.logout',
        'politica_privacidade': 'auth.politica_privacidade',  # CORRIGIDO
        'termos_uso': 'auth.termos_uso',  # Provavelmente também está no auth
        
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
        
        # Cart routes (corrected)
        'adicionar_ao_carrinho': 'cart.adicionar_ao_carrinho',
        'ver_carrinho': 'cart.carrinho',  # CORRIGIDO
        'carrinho': 'cart.carrinho',
        'remover_do_carrinho': 'cart.remover_do_carrinho',
        'atualizar_carrinho': 'cart.atualizar_carrinho',
        'remover_bolo_personalizado': 'cart.remover_bolo_personalizado',
        'atualizar_bolo_personalizado': 'cart.atualizar_bolo_personalizado',
        
        # Order routes (corrected)
        'finalizar_pedido': 'order.finalizar_pedido',
        'finalizar_compra': 'order.finalizar_compra',
        'meus_pedidos': 'order.pedidos',  # CORRIGIDO
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
        
        # Main routes (apenas para rotas que realmente estão no main)
        'contato': 'main.contato',
        'sobre': 'main.sobre',
    }
    
    print("📋 Mapeamento corrigido criado!")
    print("⚠️  Principais correções:")
    print("   • politica_privacidade: main → auth")
    print("   • termos_uso: main → auth")
    print("   • ver_carrinho: cart.ver_carrinho → cart.carrinho")
    print("   • meus_pedidos: order.meus_pedidos → order.pedidos")
    
    return corrected_mappings

def find_all_politica_references():
    """
    Encontra todas as referências a politica_privacidade
    """
    print(f"\n🔍 Procurando todas as referências a politica_privacidade...")
    
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
                        if 'politica_privacidade' in line and 'url_for' in line:
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
    print("🔧 Correção específica para politica_privacidade")
    print("=" * 60)
    
    # Mostrar o mapeamento atualizado
    corrected_mappings = update_main_script_mapping()
    
    # Fazer as correções
    fix_politica_privacidade_references()
    
    # Mostrar referências restantes
    find_all_politica_references()
    
    print(f"\n✅ Execute seu app.py novamente para verificar se o erro foi resolvido!")
    print(f"💡 Se o erro persistir, verifique em que blueprint a rota 'politica_privacidade' está realmente registrada.")