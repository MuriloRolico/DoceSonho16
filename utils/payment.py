import mysql.connector
import mercadopago
from decimal import Decimal
from flask import session

def create_mercadopago_preference(user_id, success_url, failure_url, pending_url):
    """
    Cria uma preferência de pagamento no MercadoPago com base nos itens da sessão do carrinho.
    
    Args:
        user_id: ID do usuário
        success_url: URL de retorno em caso de sucesso
        failure_url: URL de retorno em caso de falha
        pending_url: URL de retorno em caso de pagamento pendente
        
    Returns:
        O link de pagamento do MercadoPago ou None em caso de erro
    """
    # Preparar itens do carrinho a partir da sessão
    items = []
    
    if 'carrinho' in session and session['carrinho']:
        for item_id, item in session['carrinho'].items():
            items.append({
                'id': str(item['id']),
                'title': item['nome'],
                'description': item.get('descricao', 'Produto da Doce Sonho'),
                'quantity': item['quantidade'],
                'unit_price': float(item['preco']),
                'currency_id': 'BRL'
            })
    
    if 'carrinho_personalizado' in session and session['carrinho_personalizado']:
        for item_id, item in session['carrinho_personalizado'].items():
            descricao = f"Massa: {item.get('massa', '').capitalize()}"
            if 'recheios' in item:
                descricao += f", Recheios: {item['recheios']}"
            if 'cobertura' in item:
                descricao += f", Cobertura: {item['cobertura']}"
                
            items.append({
                'id': str(item['id']),
                'title': 'Bolo Personalizado',
                'description': descricao,
                'quantity': item['quantidade'],
                'unit_price': float(item['preco']),
                'currency_id': 'BRL'
            })
    
    if not items:
        return None, "Não há itens no carrinho"
    
    sdk = mercadopago.SDK("APP_USR-3186829371371378-033109-bd70da5615618f6121a56627b441334a-2363984332")
    
    request = {
        "items": items,
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url,
        }
    }
    
    try:
        preference_response = sdk.preference().create(request)
        preference = preference_response["response"]
        
        if "init_point" in preference:
            return preference["init_point"], None
        else:
            return None, "Não foi possível obter o link de pagamento"
    
    except Exception as e:
        return None, f"Erro ao criar preferência de pagamento: {str(e)}"