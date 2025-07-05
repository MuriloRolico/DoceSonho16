import os
import re

def fix_atualizar_privacidade_references(templates_dir='templates'):
    """
    Corrige especificamente as referências user.atualizar_privacidade
    """
    print("🔧 Corrigindo referências user.atualizar_privacidade...")
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
                    
                    # Substituições específicas para user.atualizar_privacidade
                    replacements = [
                        # Opção 1: Redirecionar para atualizar_perfil (sugerido pelo Flask)
                        ("url_for('user.atualizar_perfil')", "url_for('user.atualizar_perfil')"),
                        ('url_for("user.atualizar_perfil")', 'url_for("user.atualizar_perfil")'),
                        
                        # Opção 2: Se houver parâmetros, manter os parâmetros
                        ("url_for('user.atualizar_privacidade',", "url_for('user.atualizar_perfil',"),
                        ('url_for("user.atualizar_privacidade",', 'url_for("user.atualizar_perfil",'),
                        
                        # Opção 3: Se alguém usar apenas 'atualizar_privacidade'
                        ("url_for('atualizar_privacidade')", "url_for('user.atualizar_perfil')"),
                        ('url_for("atualizar_privacidade")', 'url_for("user.atualizar_perfil")'),
                        
                        # Opção 4: Variações comuns
                        ("url_for('user.privacidade')", "url_for('user.atualizar_perfil')"),
                        ('url_for("user.privacidade")', 'url_for("user.atualizar_perfil")'),
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
                        ("redirect(url_for('user.atualizar_perfil'))", "redirect(url_for('user.atualizar_perfil'))"),
                        ('redirect(url_for("user.atualizar_perfil"))', 'redirect(url_for("user.atualizar_perfil"))'),
                        ("return redirect(url_for('user.atualizar_perfil'))", "return redirect(url_for('user.atualizar_perfil'))"),
                        ('return redirect(url_for("user.atualizar_perfil"))', 'return redirect(url_for("user.atualizar_perfil"))'),
                        ("url_for('user.atualizar_perfil')", "url_for('user.atualizar_perfil')"),
                        ('url_for("user.atualizar_perfil")', 'url_for("user.atualizar_perfil")'),
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
        print(f"   'user.atualizar_privacidade' → 'user.atualizar_perfil'")
        print(f"   'atualizar_privacidade' → 'user.atualizar_perfil'")
        print(f"   'user.privacidade' → 'user.atualizar_perfil'")
        print(f"\n💡 Razão: O endpoint 'user.atualizar_privacidade' não existe.")
        print(f"   Redirecionando para 'user.atualizar_perfil' (sugerido pelo Flask).")
    else:
        print(f"\n⚠️  Nenhuma referência encontrada.")

def find_all_privacidade_references():
    """
    Encontra todas as referências a user.atualizar_privacidade
    """
    print(f"\n🔍 Procurando todas as referências a privacidade...")
    
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
                        if ('atualizar_privacidade' in line or 'user.privacidade' in line) and 'url_for' in line:
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
    print("   user.atualizar_privacidade → user.atualizar_perfil")
    print("   Motivo: Flask sugeriu este endpoint como alternativa")
    
    print("\n2️⃣ IMPLEMENTAR A FUNCIONALIDADE:")
    print("   Se você realmente precisa de configurações de privacidade,")
    print("   adicione esta rota no seu arquivo user.py:")
    
    route_code = '''
@user_bp.route('/atualizar-privacidade', methods=['GET', 'POST'])
@login_required
def atualizar_privacidade():
    """
    Atualiza as configurações de privacidade do usuário
    """
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            perfil_publico = request.form.get('perfil_publico', False)
            receber_emails = request.form.get('receber_emails', False)
            compartilhar_dados = request.form.get('compartilhar_dados', False)
            
            # Atualizar configurações no banco de dados
            current_user.perfil_publico = bool(perfil_publico)
            current_user.receber_emails = bool(receber_emails)
            current_user.compartilhar_dados = bool(compartilhar_dados)
            
            db.session.commit()
            
            flash('Configurações de privacidade atualizadas com sucesso!', 'success')
            return redirect(url_for('user.perfil'))
        
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar configurações de privacidade.', 'error')
            return redirect(url_for('user.atualizar_perfil'))
    
    return render_template('user/privacidade.html')
'''
    
    print(route_code)
    
    print("\n3️⃣ OUTRAS OPÇÕES:")
    print("   • user.atualizar_privacidade → user.perfil")
    print("   • user.atualizar_privacidade → user.dados_pessoais")
    print("   • user.atualizar_privacidade → user.editar_perfil")
    
    print("\n4️⃣ TEMPLATE NECESSÁRIO:")
    print("   Se implementar a funcionalidade, crie:")
    print("   templates/user/privacidade.html")

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
        'encerrar_todas_sessoes': 'auth.logout',
        'atualizar_privacidade': 'user.atualizar_perfil',  # NOVO: Correção adicionada
        'privacidade': 'user.atualizar_perfil',           # NOVO: Variação comum
        
        # Cart routes
        'adicionar_ao_carrinho': 'cart.adicionar_ao_carrinho',
        'ver_carrinho': 'cart.carrinho',
        'carrinho': 'cart.carrinho',
        'remover_do_carrinho': 'cart.remover_do_carrinho',
        'atualizar_carrinho': 'cart.atualizar_carrinho',
        
        # Order routes
        'finalizar_pedido': 'order.finalizar_pedido',
        'meus_pedidos': 'order.pedidos',
        'pedidos': 'order.pedidos',
        'detalhes_pedido': 'order.detalhes_pedido',
        
        # Admin routes
        'admin_dashboard': 'admin.admin_dashboard',
        'dashboard': 'admin.dashboard',
        'admin_produtos': 'admin.admin_produtos',
        'produtos': 'admin.admin_produtos',
        
        # Product routes
        'todos_produtos': 'product.todos_produtos',
        'produto_detalhes': 'product.produto_detalhes',
        # ... (resto permanece igual)
    }
    
    print("✅ Mapeamento atualizado!")
    print("   🆕 atualizar_privacidade → user.atualizar_perfil")
    print("   🆕 privacidade → user.atualizar_perfil")
    
    return updated_mappings

def create_comprehensive_fix_script():
    """
    Cria um script abrangente para corrigir múltiplos endpoints de uma vez
    """
    print(f"\n📝 Criando script abrangente...")
    
    script_content = '''import os
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
    
    print(f"\\n📊 Resumo final:")
    print(f"   📁 Arquivos modificados: {files_modified}")
    print(f"   🔄 Total de alterações: {changes_made}")

if __name__ == '__main__':
    fix_multiple_user_endpoints()
'''
    
    with open('fix_multiple_user_endpoints.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script abrangente criado: fix_multiple_user_endpoints.py")
    print("   Este script corrige múltiplos endpoints de usuário de uma vez!")

if __name__ == '__main__':
    print("🔧 Correção específica para user.atualizar_privacidade")
    print("=" * 60)
    
    # Procurar todas as referências primeiro
    find_all_privacidade_references()
    
    # Fazer as correções
    fix_atualizar_privacidade_references()
    
    # Mostrar soluções alternativas
    create_alternative_solutions()
    
    # Atualizar mapeamentos finais
    update_final_mappings()
    
    # Criar script abrangente
    create_comprehensive_fix_script()
    
    print(f"\n✅ Execute seu app.py novamente para verificar se o erro foi resolvido!")
    print(f"🎯 Se você precisar da funcionalidade real, implemente a rota sugerida.")
    print(f"📝 O script abrangente pode corrigir múltiplos endpoints de uma vez.")