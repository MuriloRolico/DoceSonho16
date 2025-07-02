// Carrinho.js - Script para atualização automática do carrinho
document.addEventListener('DOMContentLoaded', function() {
    // Seleciona todos os inputs de quantidade
    const quantidadeInputs = document.querySelectorAll('.carrinho-quantidade');
    
    // Adiciona ouvintes de evento para cada input
    quantidadeInputs.forEach(input => {
        input.addEventListener('change', atualizarValoresCarrinho);
        input.addEventListener('input', atualizarValoresCarrinho);
    });
    
    // Função que atualiza os valores do carrinho
    function atualizarValoresCarrinho() {
        let total = 0;
        
        // Itera sobre cada item do carrinho
        document.querySelectorAll('.carrinho-item').forEach(item => {
            // Obtém o preço unitário do item (removendo R$ e convertendo para número)
            const precoTexto = item.querySelector('.carrinho-preco').textContent;
            const precoUnitario = parseFloat(precoTexto.replace('R$ ', '').replace(',', '.'));
            
            // Obtém a quantidade selecionada
            const quantidade = parseInt(item.querySelector('.carrinho-quantidade').value);
            
            // Calcula o subtotal
            const subtotal = precoUnitario * quantidade;
            
            // Atualiza o texto do subtotal formatado
            item.querySelector('.carrinho-subtotal').textContent = `R$ ${subtotal.toFixed(2).replace('.', ',')}`;
            
            // Adiciona ao total
            total += subtotal;
        });
        
        // Atualiza o valor total do carrinho
        const totalElement = document.querySelector('.card-body .fs-4.fw-bold');
        if (totalElement) {
            totalElement.textContent = `R$ ${total.toFixed(2).replace('.', ',')}`;
        }
    }
    
    // Impede que o usuário digite valores menores que 1
    quantidadeInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value < 1 || !this.value) {
                this.value = 1;
                atualizarValoresCarrinho();
            }
        });
    });
});