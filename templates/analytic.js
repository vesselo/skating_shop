// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Загружаем данные с сервера
        const response = await fetch('/api/analytics/initial-data');
        
        if (!response.ok) {
            throw new Error('Ошибка загрузки данных');
        }
        
        const data = await response.json();
        
        // Инициализируем график с полученными данными
        initChart(data.labels, data.sales);
        
        // Обновляем таблицу статистики
        updateStatsTable(data.pageStats);
        
    } catch (error) {
        console.error('Ошибка инициализации:', error);
        // Показываем сообщение об ошибке пользователю
        showErrorNotification('Не удалось загрузить данные аналитики');
    }
});

// Функция инициализации графика
function initChart(labels, salesData) {
    const ctx = document.getElementById('salesChart');
    
    // Если график уже существует - уничтожаем его
    if (ctx.chartInstance) {
        ctx.chartInstance.destroy();
    }
    
    ctx.chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Сумма продаж (руб)',
                data: salesData,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('ru-RU') + ' ₽';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.raw.toLocaleString('ru-RU') + ' ₽';
                        }
                    }
                }
            }
        }
    });
}

// Функция обновления таблицы статистики
function updateStatsTable(stats) {
    const tableBody = document.querySelector('.stats-table tbody');
    tableBody.innerHTML = '';
    
    stats.forEach(item => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${escapeHtml(item.page)}</td>
            <td>${item.views.toLocaleString('ru-RU')}</td>
            <td>${item.uniqueVisitors.toLocaleString('ru-RU')}</td>
            <td>${item.conversionRate.toFixed(1)}%</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Вспомогательная функция для экранирования HTML
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Функция показа уведомления об ошибке
function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}