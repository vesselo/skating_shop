document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы управления
    const searchInput = document.getElementById('search');
    const categoryFilter = document.getElementById('category-filter');
    const priceSort = document.getElementById('price-sort');
    const productContainer = document.querySelector('.products');
    let productCards = Array.from(document.querySelectorAll('.product-card'));
    
    // Функция для применения фильтров
    function applyFilters() {
        const searchTerm = searchInput.value.toLowerCase();
        const category = categoryFilter.value;
        const sortBy = priceSort.value;
        
        // Фильтрация
        let filteredProducts = productCards.filter(card => {
            const matchesSearch = searchTerm ? 
                card.querySelector('h3').textContent.toLowerCase().includes(searchTerm) : true;
            const matchesCategory = category !== 'all' ? 
                card.dataset.category === category : true;
            return matchesSearch && matchesCategory;
        });
        
        // Сортировка
        if (sortBy !== 'default') {
            filteredProducts.sort((a, b) => {
                const priceA = parseFloat(a.dataset.price);
                const priceB = parseFloat(b.dataset.price);
                return sortBy === 'asc' ? priceA - priceB : priceB - priceA;
            });
        }
        
        // Обновляем отображение
        updateProductDisplay(filteredProducts);
    }
    
    // Функция обновления отображения товаров
    function updateProductDisplay(filteredProducts) {
        // Сначала скрываем все карточки
        productCards.forEach(card => {
            card.style.display = 'none';
            card.style.order = '0';
        });
        
        // Показываем и упорядочиваем отфильтрованные карточки
        filteredProducts.forEach((card, index) => {
            card.style.display = 'block';
            card.style.order = index;
        });
        
        // Анимация перестроения
        productContainer.style.opacity = '0.5';
        setTimeout(() => {
            productContainer.style.opacity = '1';
        }, 300);
    }
    
    // Обработчики событий для мгновенного применения фильтров
    searchInput.addEventListener('input', debounce(applyFilters, 300));
    categoryFilter.addEventListener('change', applyFilters);
    priceSort.addEventListener('change', applyFilters);
    
    // Функция для дебаунса (задержки обработки ввода)
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this, args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        };
    }
    
    // Обработчик добавления в корзину
    document.querySelector('.products').addEventListener('click', function(e) {
        if (e.target.classList.contains('add-to-cart')) {
            const productId = e.target.dataset.id;
            addToCart(productId);
        }
    });
    
    // Функция добавления в корзину
    function addToCart(productId) {
        fetch('/api/add_to_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: 1
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showCartNotification('Товар добавлен в корзину');
                updateCartCount(data.cart_count);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    
    // Функция показа уведомления
    function showCartNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'cart-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    // Функция обновления счетчика корзины
    function updateCartCount(count) {
        const cartCount = document.querySelector('.cart-count');
        if (cartCount) {
            cartCount.textContent = count;
            cartCount.classList.add('animate');
            setTimeout(() => {
                cartCount.classList.remove('animate');
            }, 500);
        }
    }
    
    // Инициализация
    applyFilters();
});