// Aguarda o carregamento completo do DOM
document.addEventListener('DOMContentLoaded', function() {
    // === CONFIGURAÇÃO INICIAL ===
    // Inicializa tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // === ANIMAÇÕES DE ENTRADA ===
    // Animação suave para elementos quando a página carregar
    const animateElements = document.querySelectorAll('.produto-card, .newsletter, h1, h2, .intro-message');
    animateElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 100 + (index * 100));
    });

    // === FUNCIONALIDADE DE FILTROS E BUSCA ===
    const produtos = document.querySelectorAll('.produto-card');
    const filtroCategoriaSelect = document.getElementById('filtro-categoria');
    const filtroPrecoSelect = document.getElementById('filtro-preco');
    const buscaProdutoInput = document.getElementById('busca-produto');
    const buscaBotao = buscaProdutoInput?.nextElementSibling;

    // Função para filtrar produtos
    function filtrarProdutos() {
        const categoriaFiltro = filtroCategoriaSelect.value;
        const precoFiltro = filtroPrecoSelect.value;
        const termoBusca = buscaProdutoInput.value.toLowerCase();
        
        // Captura todos os produtos para reordenar se necessário
        let produtosArray = Array.from(produtos);
        
        // Ordenar por preço se selecionado
        if (precoFiltro) {
            produtosArray.sort((a, b) => {
                const precoA = parseFloat(a.querySelector('.preco').textContent.replace('R$ ', '').replace(',', '.'));
                const precoB = parseFloat(b.querySelector('.preco').textContent.replace('R$ ', '').replace(',', '.'));
                
                return precoFiltro === 'menor' ? precoA - precoB : precoB - precoA;
            });
            
            // Reordenar na DOM
            const grid = document.querySelector('.produto-grid');
            produtosArray.forEach(produto => {
                grid.appendChild(produto.parentElement);
            });
        }
        
        // Filtrar por categoria e busca
        produtos.forEach(produto => {
            const card = produto;
            const categoria = card.querySelector('.badge').textContent.toLowerCase();
            const nome = card.querySelector('.card-title').textContent.toLowerCase();
            const descricao = card.querySelector('.card-text').textContent.toLowerCase();
            
            const matchCategoria = !categoriaFiltro || categoria.includes(categoriaFiltro);
            const matchBusca = !termoBusca || 
                nome.includes(termoBusca) || 
                descricao.includes(termoBusca);
            
            if (matchCategoria && matchBusca) {
                card.parentElement.style.display = '';
            } else {
                card.parentElement.style.display = 'none';
            }
        });
    }

    // Adicionar event listeners para filtros
    if (filtroCategoriaSelect) filtroCategoriaSelect.addEventListener('change', filtrarProdutos);
    if (filtroPrecoSelect) filtroPrecoSelect.addEventListener('change', filtrarProdutos);
    if (buscaProdutoInput) buscaProdutoInput.addEventListener('keyup', filtrarProdutos);
    if (buscaBotao) buscaBotao.addEventListener('click', filtrarProdutos);

    // === MELHORIAS NO FORMULÁRIO DE NEWSLETTER ===
    const newsletterForm = document.querySelector('.newsletter .input-group');
    if (newsletterForm) {
        const newsletterBtn = newsletterForm.querySelector('button');
        const newsletterInput = newsletterForm.querySelector('input');
        
        newsletterBtn.addEventListener('click', function() {
            const email = newsletterInput.value.trim();
            
            if (email && isValidEmail(email)) {
                // Simular envio (não afeta o backend)
                newsletterBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Cadastrando...';
                
                setTimeout(() => {
                    newsletterInput.value = '';
                    newsletterBtn.textContent = 'Cadastrar';
                    
                    // Criar mensagem de sucesso
                    const successMessage = document.createElement('div');
                    successMessage.className = 'alert alert-success mt-3 animated fadeIn';
                    successMessage.textContent = 'E-mail cadastrado com sucesso! Obrigado.';
                    newsletterForm.parentElement.appendChild(successMessage);
                    
                    // Remover mensagem após 5 segundos
                    setTimeout(() => {
                        successMessage.style.opacity = '0';
                        successMessage.style.transition = 'opacity 0.5s ease';
                        setTimeout(() => successMessage.remove(), 500);
                    }, 5000);
                }, 1500);
                
            } else {
                newsletterInput.classList.add('is-invalid');
                
                // Criar mensagem de erro se não existir
                if (!document.querySelector('.newsletter .invalid-feedback')) {
                    const errorMessage = document.createElement('div');
                    errorMessage.className = 'invalid-feedback';
                    errorMessage.textContent = 'Por favor, insira um e-mail válido.';
                    newsletterInput.parentNode.appendChild(errorMessage);
                }
            }
        });
        
        // Remover classe de erro quando o usuário começa a digitar novamente
        newsletterInput.addEventListener('input', function() {
            newsletterInput.classList.remove('is-invalid');
        });
    }

    // === APRIMORAR FORMULÁRIO DE CONTATO ===
    const contatoForm = document.getElementById('contato-form');
    if (contatoForm) {
        contatoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const nome = this.querySelector('input[type="text"]').value;
            const email = this.querySelector('input[type="email"]').value;
            const mensagem = this.querySelector('textarea').value;
            
            // Validação básica
            if (!nome || !email || !mensagem || !isValidEmail(email)) {
                alert('Por favor, preencha todos os campos corretamente.');
                return;
            }
            
            // Substituir o botão por um spinner durante o "envio"
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enviando...';
            submitBtn.disabled = true;
            
            // Simular envio (sem afetar o backend)
            setTimeout(() => {
                // Mostrar mensagem de sucesso
                const successAlert = document.createElement('div');
                successAlert.className = 'alert alert-success mt-3';
                successAlert.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i>Mensagem enviada com sucesso! Entraremos em contato em breve.';
                contatoForm.appendChild(successAlert);
                
                // Resetar formulário
                contatoForm.reset();
                
                // Restaurar botão
                submitBtn.innerHTML = originalBtnText;
                submitBtn.disabled = false;
                
                // Remover alerta após 5 segundos
                setTimeout(() => {
                    successAlert.style.opacity = '0';
                    successAlert.style.transition = 'opacity 0.5s ease';
                    setTimeout(() => successAlert.remove(), 500);
                }, 5000);
            }, 1500);
        });
    }

    // === EFEITOS VISUAIS NOS CARDS DE PRODUTOS ===
    produtos.forEach(produto => {
        // Efeito hover mais suave
        produto.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
            this.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
        });
        
        produto.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        });
        
        // Adicionar botão de visualização rápida
        const cardBody = produto.querySelector('.card-body');
        const imgContainer = produto.querySelector('.card-img-top').parentElement;
        
        const quickViewBtn = document.createElement('button');
        quickViewBtn.className = 'btn btn-sm btn-light position-absolute top-0 end-0 m-2';
        quickViewBtn.innerHTML = '<i class="bi bi-eye"></i>';
        quickViewBtn.setAttribute('data-bs-toggle', 'tooltip');
        quickViewBtn.setAttribute('data-bs-title', 'Visualização rápida');
        imgContainer.style.position = 'relative';
        imgContainer.appendChild(quickViewBtn);
        
        // Event listener para o botão de visualização rápida
        quickViewBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const nome = produto.querySelector('.card-title').textContent;
            const categoria = produto.querySelector('.badge').textContent;
            const descricao = produto.querySelector('.card-text').textContent;
            const preco = produto.querySelector('.preco').textContent;
            const imagem = produto.querySelector('.card-img-top').src;
            
            createQuickViewModal(nome, categoria, descricao, preco, imagem);
        });
    });

    // === AUTO FECHAR ALERTAS FLASH ===
    const flashAlerts = document.querySelectorAll('.alert-dismissible');
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = new bootstrap.Alert(alert);
            closeButton.close();
        }, 5000);
    });

    // === MELHORIAS NO BOTÃO WHATSAPP ===
    const whatsappBtn = document.querySelector('.whatsapp-float a');
    if (whatsappBtn) {
        // Adicionar tooltip
        whatsappBtn.setAttribute('data-bs-toggle', 'tooltip');
        whatsappBtn.setAttribute('data-bs-title', 'Fale conosco pelo WhatsApp');
        
        // Adicionar animação de pulso
        whatsappBtn.classList.add('pulse');
        const style = document.createElement('style');
        style.textContent = `
            .pulse {
                animation: pulse-animation 2s infinite;
            }
            
            @keyframes pulse-animation {
                0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
                100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
            }
        `;
        document.head.appendChild(style);
    }

    // === FUNÇÕES AUXILIARES ===
    
    // Validar formato de e-mail
    function isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    // Criar modal de visualização rápida
    function createQuickViewModal(nome, categoria, descricao, preco, imagem) {
        // Remover modal existente se houver
        const existingModal = document.getElementById('quickViewModal');
        if (existingModal) existingModal.remove();
        
        // Criar estrutura do modal
        const modalHTML = `
            <div class="modal fade" id="quickViewModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${nome}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <img src="${imagem}" class="img-fluid rounded mb-3" alt="${nome}">
                                </div>
                                <div class="col-md-6">
                                    <div class="badge bg-primary mb-2">${categoria}</div>
                                    <p>${descricao}</p>
                                    <h4 class="my-3">${preco}</h4>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                            <button type="button" class="btn btn-primary adicionar-carrinho-modal">
                                <i class="bi bi-cart-plus"></i> Adicionar ao Carrinho
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Adicionar modal ao DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Exibir modal
        const modalElement = document.getElementById('quickViewModal');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        
        // Adicionar evento ao botão de adicionar ao carrinho
        const addToCartBtn = modalElement.querySelector('.adicionar-carrinho-modal');
        addToCartBtn.addEventListener('click', function() {
            // Encontrar URL original de adicionar ao carrinho
            const originalAddBtn = Array.from(produtos).find(p => 
                p.querySelector('.card-title').textContent === nome
            ).querySelector('a.btn-primary');
            
            // Redirecionar para a URL original (preservando a funcionalidade original)
            window.location.href = originalAddBtn.href;
        });
    }

    // === LAZY LOADING PARA IMAGENS ===
    document.querySelectorAll('.card-img-top').forEach(img => {
        img.loading = 'lazy';
    });

    // === ADICIONAR ANIMAÇÃO DE CONTAGEM PARA TOTAIS ===
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counters = entry.target.querySelectorAll('.counter');
                counters.forEach(counter => {
                    const target = parseInt(counter.getAttribute('data-target'));
                    const duration = 2000;
                    const increment = target / (duration / 16);
                    let current = 0;
                    
                    const updateCounter = () => {
                        current += increment;
                        counter.textContent = Math.round(current);
                        if (current < target) {
                            requestAnimationFrame(updateCounter);
                        } else {
                            counter.textContent = target;
                        }
                    };
                    
                    updateCounter();
                });
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    // Observar elementos com contadores se existirem
    document.querySelectorAll('.stats-container').forEach(container => {
        observer.observe(container);
    });
});