document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    const btnCarrinhoToggle = document.querySelector('.btn-carrinho-toggle');
    const carrinho = document.querySelector('.carrinho');
    const fecharCarrinho = document.querySelector('.fechar-carrinho');
    const overlay = document.querySelector('.overlay');
    const contadorCarrinho = document.querySelector('.contador-carrinho');
    const carrinhoItens = document.querySelector('.carrinho-itens');
    const carrinhoTotal = document.querySelector('.carrinho-total-valor');
    const btnFinalizarCompra = document.querySelector('.btn-finalizar');
    const modal = document.querySelector('.modal');
    const fecharModal = document.querySelector('.fechar-modal');
    const btnAddCarrinho = document.querySelectorAll('.btn-add-carrinho');
    
    // Estado do carrinho
    let carrinhoItems = [];
    
    // Toggle menu mobile
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('aberto');
            overlay.classList.toggle('ativo');
        });
    }
    
    // Fechar menu ao clicar em um link
    const links = document.querySelectorAll('.nav-links a');
    links.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.classList.remove('aberto');
            overlay.classList.remove('ativo');
        });
    });

    // Abrir carrinho
    if (btnCarrinhoToggle) {
        btnCarrinhoToggle.addEventListener('click', function() {
            carrinho.classList.add('aberto');
            overlay.classList.add('ativo');
        });
    }
    
    // Fechar carrinho
    if (fecharCarrinho) {
        fecharCarrinho.addEventListener('click', function() {
            carrinho.classList.remove('aberto');
            overlay.classList.remove('ativo');
        });
    }
    
    // Fechar ao clicar no overlay
    if (overlay) {
        overlay.addEventListener('click', function() {
            carrinho.classList.remove('aberto');
            navLinks.classList.remove('aberto');
            modal.classList.remove('ativo');
            overlay.classList.remove('ativo');
        });
    }
    
    // Adicionar ao carrinho
    if (btnAddCarrinho) {
        btnAddCarrinho.forEach(btn => {
            btn.addEventListener('click', function() {
                const produtoCard = this.closest('.produto-card');
                const id = produtoCard.dataset.id;
                const nome = produtoCard.querySelector('.produto-nome').textContent;
                const preco = parseFloat(produtoCard.querySelector('.produto-preco').textContent.replace('R$', '').replace(',', '.'));
                const img = produtoCard.querySelector('.produto-img').src;
                
                adicionarAoCarrinho(id, nome, preco, img);
                
                // Mostrar notificação
                mostrarNotificacao(`${nome} adicionado ao carrinho!`);
            });
        });
    }
    
    // Função para adicionar ao carrinho
    function adicionarAoCarrinho(id, nome, preco, img) {
        const itemExistente = carrinhoItems.find(item => item.id === id);
        
        if (itemExistente) {
            itemExistente.quantidade += 1;
        } else {
            carrinhoItems.push({
                id,
                nome,
                preco,
                img,
                quantidade: 1
            });
        }
        
        atualizarCarrinho();
    }
    
    // Função para atualizar o carrinho
    function atualizarCarrinho() {
        // Limpar o carrinho
        carrinhoItens.innerHTML = '';
        
        let total = 0;
        let quantidadeTotal = 0;
        
        carrinhoItems.forEach(item => {
            const itemTotal = item.preco * item.quantidade;
            total += itemTotal;
            quantidadeTotal += item.quantidade;
            
            // Criar elemento do item
            const itemElement = document.createElement('div');
            itemElement.classList.add('carrinho-item');
            itemElement.innerHTML = `
                <img src="${item.img}" alt="${item.nome}" class="carrinho-item-img">
                <div class="carrinho-item-info">
                    <div class="carrinho-item-nome">${item.nome}</div>
                    <div class="carrinho-item-preco">R$ ${item.preco.toFixed(2).replace('.', ',')}</div>
                    <div class="carrinho-item-qtd">
                        <button class="qtd-btn menos" data-id="${item.id}">-</button>
                        <span class="qtd-valor">${item.quantidade}</span>
                        <button class="qtd-btn mais" data-id="${item.id}">+</button>
                    </div>
                </div>
                <div class="carrinho-item-total">
                    R$ ${itemTotal.toFixed(2).replace('.', ',')}
                </div>
                <button class="remover-item" data-id="${item.id}">×</button>
            `;
            
            carrinhoItens.appendChild(itemElement);
        });
        
        // Atualizar total
        if (carrinhoTotal) {
            carrinhoTotal.textContent = `R$ ${total.toFixed(2).replace('.', ',')}`;
        }
        
        // Atualizar contador
        if (contadorCarrinho) {
            contadorCarrinho.textContent = quantidadeTotal;
            contadorCarrinho.style.display = quantidadeTotal > 0 ? 'flex' : 'none';
        }
        
        // Adicionar eventos aos botões
        adicionarEventosBotoesCarrinho();
        
        // Salvar no localStorage
        localStorage.setItem('carrinhoItems', JSON.stringify(carrinhoItems));
    }
    
    // Função para adicionar eventos aos botões do carrinho
    function adicionarEventosBotoesCarrinho() {
        // Botões de aumentar quantidade
        const btnMais = document.querySelectorAll('.mais');
        btnMais.forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.dataset.id;
                const item = carrinhoItems.find(item => item.id === id);
                if (item) {
                    item.quantidade += 1;
                    atualizarCarrinho();
                }
            });
        });
        
        // Botões de diminuir quantidade
        const btnMenos = document.querySelectorAll('.menos');
        btnMenos.forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.dataset.id;
                const item = carrinhoItems.find(item => item.id === id);
                if (item && item.quantidade > 1) {
                    item.quantidade -= 1;
                    atualizarCarrinho();
                } else if (item && item.quantidade === 1) {
                    removerDoCarrinho(id);
                }
            });
        });
        
        // Botões de remover item
        const btnRemover = document.querySelectorAll('.remover-item');
        btnRemover.forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.dataset.id;
                removerDoCarrinho(id);
            });
        });
    }
    
    // Função para remover do carrinho
    function removerDoCarrinho(id) {
        carrinhoItems = carrinhoItems.filter(item => item.id !== id);
        atualizarCarrinho();
    }
    
    // Finalizar compra
    if (btnFinalizarCompra) {
        btnFinalizarCompra.addEventListener('click', function() {
            if (carrinhoItems.length > 0) {
                // Exibir modal de sucesso
                modal.classList.add('ativo');
                overlay.classList.add('ativo');
                
                // Limpar carrinho
                carrinhoItems = [];
                atualizarCarrinho();
                
                // Fechar carrinho
                carrinho.classList.remove('aberto');
            } else {
                alert('Seu carrinho está vazio!');
            }
        });
    }
    
    // Fechar modal
    if (fecharModal) {
        fecharModal.addEventListener('click', function() {
            modal.classList.remove('ativo');
            overlay.classList.remove('ativo');
        });
    }
    
    // Função para mostrar notificação
    function mostrarNotificacao(mensagem) {
        // Criar elemento
        const notificacao = document.createElement('div');
        notificacao.classList.add('notificacao');
        notificacao.textContent = mensagem;
        
        // Adicionar ao DOM
        document.body.appendChild(notificacao);
        
        // Adicionar classe para animar
        setTimeout(() => {
            notificacao.classList.add('ativo');
        }, 10);
        
        // Remover após 3 segundos
        setTimeout(() => {
            notificacao.classList.remove('ativo');
            setTimeout(() => {
                notificacao.remove();
            }, 300);
        }, 3000);
    }
    
    // Carregar carrinho do localStorage
    function carregarCarrinho() {
        const carrinhoSalvo = localStorage.getItem('carrinhoItems');
        if (carrinhoSalvo) {
            carrinhoItems = JSON.parse(carrinhoSalvo);
            atualizarCarrinho();
        }
    }
    
    // Animação de scroll suave
    const scrollLinks = document.querySelectorAll('a[href^="#"]');
    scrollLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Animação de elementos ao scroll
    function animarAoScroll() {
        const elementos = document.querySelectorAll('.animar');
        const windowHeight = window.innerHeight;
        
        elementos.forEach(elemento => {
            const posicaoElemento = elemento.getBoundingClientRect().top;
            
            if (posicaoElemento - windowHeight <= 0) {
                elemento.classList.add('fadeIn');
            }
        });
    }
    
    // Adicionar classe 'animar' aos elementos para animação
    function prepararAnimacoes() {
        const produtosCards = document.querySelectorAll('.produto-card');
        produtosCards.forEach(card => {
            card.classList.add('animar');
        });
        
        const secoes = document.querySelectorAll('.sobre, .produtos-titulo, .formulario-contato');
        secoes.forEach(secao => {
            secao.classList.add('animar');
        });
    }

    // Inicializar funções
    carregarCarrinho();
    prepararAnimacoes();
    animarAoScroll();
    
    // Executar animação ao scroll
    window.addEventListener('scroll', animarAoScroll);
        
    // Adicione a notificação CSS ao documento
    const notificacaoCSS = document.createElement('style');
    notificacaoCSS.textContent = `
        .notificacao {
            position: fixed;
            bottom: -60px;
            left: 50%;
            transform: translateX(-50%);
            background-color: var(--cor-destaque);
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 30px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            opacity: 0;
            transition: all 0.3s ease;
        }
        
        .notificacao.ativo {
            bottom: 30px;
            opacity: 1;
        }
    `;
    document.head.appendChild(notificacaoCSS);
});