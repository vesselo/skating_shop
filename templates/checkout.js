document.addEventListener('DOMContentLoaded', function() {
    const checkoutForm = document.getElementById('checkout-form');
    
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // В реальном приложении здесь была бы валидация формы
            // и отправка данных на сервер
            
            this.submit(); // Отправляем форму
        });
    }
});