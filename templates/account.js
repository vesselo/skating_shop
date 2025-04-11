document.addEventListener('DOMContentLoaded', function() {
    // Переключение между вкладками
    const tabLinks = document.querySelectorAll('.account-sidebar a');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Убираем активный класс у всех ссылок и вкладок
            tabLinks.forEach(l => l.parentNode.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Добавляем активный класс к текущей ссылке
            this.parentNode.classList.add('active');
            
            // Показываем соответствующую вкладку
            const tabId = this.getAttribute('href').substring(1);
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Обработчик для кнопки "Подробности о заказах"
    const orderDetailsBtn = document.querySelector('.btn-order-details');
    if (orderDetailsBtn) {
        orderDetailsBtn.addEventListener('click', function() {
            window.location.href = '/orders_history';
        });
    }
    
    // Редактирование профиля
    const editProfileBtn = document.querySelector('.edit-profile');
    const userInfo = document.querySelector('.user-info');
    
    if (editProfileBtn) {
        editProfileBtn.addEventListener('click', function() {
            const isEditing = userInfo.classList.toggle('editing');
            
            if (isEditing) {
                this.textContent = 'Сохранить изменения';
                
                // Заменяем текстовые поля на input'ы для редактирования
                const fields = userInfo.querySelectorAll('p');
                fields.forEach(field => {
                    const text = field.textContent.split(': ')[1];
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.value = text;
                    field.innerHTML = field.textContent.split(': ')[0] + ': ';
                    field.appendChild(input);
                });
            } else {
                this.textContent = 'Редактировать профиль';
                
                // Сохраняем изменения (в реальном приложении отправляем на сервер)
                const inputs = userInfo.querySelectorAll('input');
                inputs.forEach(input => {
                    const field = input.parentNode;
                    field.innerHTML = field.textContent.split(': ')[0] + ': ' + input.value;
                });
            }
        });
    }

// Отменить заказ
document.querySelectorAll('.cancel-order').forEach(btn => {
    btn.addEventListener('click', function() {
        if(confirm('Вы уверены, что хотите отменить заказ?')) {
            const orderId = this.dataset.orderId;
            fetch(`/api/cancel_order/${orderId}`, {
                method: 'POST'
            }).then(response => {
                if(response.ok) {
                    location.reload();
                }
            });
        }
    });
});
});