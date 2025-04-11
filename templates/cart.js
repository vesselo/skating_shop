document.addEventListener('DOMContentLoaded', function() {
    // Изменение количества товара
    const quantityInputs = document.querySelectorAll('.quantity-input');
    
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const productId = this.dataset.id;
            const quantity = parseInt(this.value);
            
            fetch('/api/update_cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        });
    });
    
    document.querySelectorAll('.remove-from-cart').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-id');
            const row = this.closest('tr');
            
            fetch('/api/remove_from_cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ product_id: productId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Удаляем строку с товаром из таблицы
                    row.remove();
                    
                    // Обновляем общую сумму
                    updateCartTotal();
                    
                    // Обновляем счетчик корзины в шапке сайта
                    updateCartCount(data.cart_count);
                    
                    // Если корзина пуста, показываем сообщение
                    if (data.is_empty) {
                        document.querySelector('.cart-items').innerHTML = `
                            <div class="empty-cart-message">
                                <p>Ваша корзина пуста</p>
                                <a href="/catalog" class="btn">Перейти в каталог</a>
                            </div>
                        `;
                        document.querySelector('.cart-actions').style.display = 'none';
                    }
                } else {
                    alert('Ошибка: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при удалении товара');
            });
        });
    });
    
    // Функция для обновления общей суммы
    function updateCartTotal() {
        let total = 0;
        document.querySelectorAll('tbody tr').forEach(row => {
            const price = parseFloat(row.querySelector('td:nth-child(2)').textContent);
            const quantity = parseInt(row.querySelector('.quantity-input').value);
            const subtotal = price * quantity;
            row.querySelector('td:nth-child(4)').textContent = subtotal.toFixed(2) + ' руб.';
            total += subtotal;
        });
        document.querySelector('tfoot td:last-child').textContent = total.toFixed(2) + ' руб.';
    }
    
    // Функция для обновления счетчика в шапке
    function updateCartCount(count) {
        const cartCounter = document.querySelector('.cart-counter');
        if (cartCounter) {
            cartCounter.textContent = count;
            cartCounter.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('checkout-form');
        
        if (form) {
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('button[type="submit"]');
                
                // Валидация формы перед отправкой
                const requiredFields = this.querySelectorAll('[required]');
                let isValid = true;
                
                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        field.style.borderColor = 'red';
                        isValid = false;
                    } else {
                        field.style.borderColor = '';
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    alert('Пожалуйста, заполните все обязательные поля');
                    return;
                }
                
                // Показываем состояние загрузки
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Оформление...';
            });
        }
        
        // Прячем уведомление через 5 секунд
        const alert = document.getElementById('order-alert');
        if (alert) {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }, 5000);
        }
    });
});