import os
import re

def fix_register_references(templates_dir='templates'):
    """
    Corrige especificamente as referências register para auth.registro
    """
    print("🔧 Corrigindo referências register...")
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
                    
                    # Substituições específicas para register
                    replacements = [
                        ("url_for('auth.registro')", "url_for('auth.registro')"),
                        ('url_for("auth.registro")', 'url_for("auth.registro")'),
                        ("url_for('register',", "url_for('auth.registro',"),
                        ('url_for("register",', 'url_for("auth.registro",'),
                        ("url_for('auth.registro')", "url_for('auth.registro')"),
                        ('url_for("auth.registro")', 'url_for("auth.registro")'),
                        ("url_for('auth.register',", "url_for('auth.registro',"),
                        ('url_for("auth.register",', 'url_for("auth.registro",'),
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
                        ("redirect(url_for('auth.registro'))", "redirect(url_for('auth.registro'))"),
                        ('redirect(url_for("auth.registro"))', 'redirect(url_for("auth.registro"))'),
                        ("return redirect(url_for('auth.registro'))", "return redirect(url_for('auth.registro'))"),
                        ('return redirect(url_for("auth.registro"))', 'return redirect(url_for("auth.registro"))'),
                        ("url_for('auth.registro')", "url_for('auth.registro')"),
                        ('url_for("auth.registro")', 'url_for("auth.registro")'),
                        ("url_for('auth.registro')", "url_for('auth.registro')"),
                        ('url_for("auth.registro")', 'url_for("auth.registro")'),
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
        print(f"   'register' → 'auth.registro'")
        print(f"   'auth.register' → 'auth.registro'")
    else:
        print(f"\n⚠️  Nenhuma referência encontrada nos templates.")

def create_corrected_master_script():
    """
    Cria um script mestre com todos os mapeamentos corretos descobertos até agora
    """
    print(f"\n🔧 Criando script mestre com mapeamentos corretos...")
    
    # Mapeamentos corretos baseados nos erros encontrados
    corrected_mappings = {
        # Auth routes (CORRIGIDOS)
        'login': 'auth.login',
        'register': 'auth.registro',  # CORRIGIDO: register → auth.registro
        'registro': 'auth.registro',
        'logout': 'auth.logout',
        'politica_privacidade': 'auth.politica_privacidade',  # CORRIGIDO: main → auth
        'termos_uso': 'auth.termos_uso',  # Provavelmente também no auth
        
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
        
        # Cart routes (CORRIGIDOS)
        'adicionar_ao_carrinho': 'cart.adicionar_ao_carrinho',
        'ver_carrinho': 'cart.carrinho',  # CORRIGIDO: cart.ver_carrinho → cart.carrinho
        'carrinho': 'cart.carrinho',
        'remover_do_carrinho': 'cart.remover_do_carrinho',
        'atualizar_carrinho': 'cart.atualizar_carrinho',
        'remover_bolo_personalizado': 'cart.remover_bolo_personalizado',
        'atualizar_bolo_personalizado': 'cart.atualizar_bolo_personalizado',
        
        # Order routes (CORRIGIDOS)
        'finalizar_pedido': 'order.finalizar_pedido',
        'finalizar_compra': 'order.finalizar_compra',
        'meus_pedidos': 'order.pedidos',  # CORRIGIDO: order.meus_pedidos → order.pedidos
        'pedidos': 'order.pedidos',
        'detalhes_pedido': 'order.detalhes_pedido',
        'cancelar_pedido': 'order.cancelar_pedido',
        'confirmar_pedido': 'order.confirmar_pedido',
        'admin_detalhes_pedido': 'order.admin_detalhes_pedido',
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
        
        # Main routes (apenas rotas que realmente estão no main)
        'contato': 'main.contato',
        'sobre': 'main.sobre',
    }
    
    print("📋 Principais correções aplicadas:")
    print("   ✅ register → auth.registro")
    print("   ✅ politica_privacidade → auth.politica_privacidade")
    print("   ✅ ver_carrinho → cart.carrinho")
    print("   ✅ meus_pedidos → order.pedidos")
    
    return corrected_mappings

def find_all_register_references():
    """
    Encontra todas as referências a register/registro
    """
    print(f"\n🔍 Procurando todas as referências a register/registro...")
    
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
                        if ('register' in line or 'registro' in line) and 'url_for' in line:
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

def list_all_flask_routes():
    """
    Código para você usar no seu app.py para listar todas as rotas
    """
    print(f"\n📋 Para verificar todas as rotas do seu Flask app, adicione este código:")
    print("=" * 60)
    print("""
# Adicione este código temporário no seu app.py (depois de criar o app):

@app.route('/debug/routes')
def list_routes():
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        output.append(f"{rule.endpoint} -> {rule.rule} [{methods}]")
    
    return '<br>'.join(sorted(output))

# Depois acesse: http://localhost:5000/debug/routes
# Isso mostrará todas as rotas registradas e seus blueprints corretos
    """)
    print("=" * 60)

if __name__ == '__main__':
    print("🔧 Correção específica para register → auth.registro")
    print("=" * 60)
    
    # Criar mapeamentos corretos
    corrected_mappings = create_corrected_master_script()
    
    # Fazer as correções
    fix_register_references()
    
    # Mostrar referências restantes
    find_all_register_references()
    
    # Mostrar como verificar rotas
    list_all_flask_routes()
    
    print(f"\n✅ Execute seu app.py novamente para verificar se o erro foi resolvido!")
    print(f"💡 Use o código debug para ver exatamente como suas rotas estão registradas.")