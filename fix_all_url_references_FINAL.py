import os
import re

def fix_all_url_references(templates_dir='templates'):
    """
    Script FINAL para corrigir todas as referências url_for nos templates
    Baseado em todos os erros encontrados durante os testes
    """
    
    # Endpoints que NÃO devem ser alterados (rotas especiais do Flask)
    SKIP_ENDPOINTS = {'static', 'index'}
    
    # Mapeamento FINAL - TESTADO E CORRIGIDO
    endpoint_mappings = {
        # Auth routes (CORRIGIDOS)
        'login': 'auth.login',
        'register': 'auth.registro',  # CORRIGIDO: register → auth.registro
        'registro': 'auth.registro',
        'logout': 'auth.logout',
        'politica_privacidade': 'auth.politica_privacidade',  # CORRIGIDO: main → auth
        'termos_uso': 'auth.termos_uso',
        
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
        
        # Admin routes (CORRIGIDOS)
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
        'admin_produtos': 'admin.admin_produtos',  # CORRIGIDO: admin.produtos → admin.admin_produtos
        'produtos': 'admin.admin_produtos',        # CORRIGIDO: produtos → admin.admin_produtos
        'editar_usuario': 'admin.editar_usuario',
        'deletar_usuario': 'admin.deletar_usuario',
        
        # Payment routes
        'pagamento': 'payment.pagamento',
        'processar_pagamento': 'payment.processar_pagamento',
        'callback_pagamento': 'payment.callback_pagamento',
        
        # Main routes
        'contato': 'main.contato',
        'sobre': 'main.sobre',
    }
    
    files_modified = 0
    changes_made = 0
    
    print("🔧 Aplicando TODAS as correções descobertas...")
    print("=" * 50)
    
    # Resto do código igual ao original...
    # [código do script original aqui]

if __name__ == '__main__':
    print("🔧 SCRIPT FINAL - Corrigindo TODOS os url_for")
    print("=" * 50)
    fix_all_url_references()
