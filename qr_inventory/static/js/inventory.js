document.getElementById('plannedInventoryForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    fetch('/inventory/planned', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            startDate: startDate,
            endDate: endDate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Сначала обновляем статус инвентаризации
            fetch('/inventory/check_active')
                .then(response => response.json())
                .then(statusData => {
                    // После подтверждения статуса перенаправляем
                    window.location.href = '/inventory/current';
                })
                .catch(error => {
                    console.error('Error checking status:', error);
                    window.location.href = '/inventory/current';
                });
        } else {
            alert('Ошибка: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при создании инвентаризации');
    });
});

// Добавляем проверку при отправке форм
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', async function(e) {
        if (this.id === 'plannedInventoryForm') return; // Пропускаем форму плановой инвентаризации
        
        e.preventDefault();
        
        // Проверяем наличие активной инвентаризации
        const response = await fetch('/inventory/check_active');
        const data = await response.json();
        
        if (!data.has_active) {
            // Если активной инвентаризации нет, отправляем форму
            this.submit();
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Устанавливаем минимальную дату как сегодня
    var today = new Date().toISOString().split('T')[0];
    
    // Установка даты для формы внеплановой инвентаризации
    const startDateInput = document.getElementById('start_date');
    if (startDateInput) {
        startDateInput.min = today;
        startDateInput.value = today;
    }
    
    // Установка даты для формы плановой инвентаризации
    const plannedStartDateInput = document.getElementById('startDate');
    const plannedEndDateInput = document.getElementById('endDate');
    if (plannedStartDateInput) {
        plannedStartDateInput.min = today;
        plannedStartDateInput.value = today;
    }
    if (plannedEndDateInput) {
        plannedEndDateInput.min = today;
        plannedEndDateInput.value = today;
    }

    // Функция для проверки статуса инвентаризации
    function checkInventoryStatus() {
        fetch('/inventory/check_active')
            .then(response => response.json())
            .then(data => {
                const plannedBtn = document.querySelector('[data-bs-target="#plannedInventoryModal"]');
                const unplannedBtn = document.querySelector('[data-bs-target="#unplannedModal"]');
                
                if (!plannedBtn || !unplannedBtn) return;
                
                if (data.has_active) {
                    plannedBtn.disabled = true;
                    unplannedBtn.disabled = true;
                    plannedBtn.title = "Невозможно начать новую инвентаризацию, пока не завершена текущая";
                    unplannedBtn.title = "Невозможно начать новую инвентаризацию, пока не завершена текущая";
                    if (!plannedBtn.querySelector('.fas.fa-lock')) {
                        plannedBtn.innerHTML = '<i class="fas fa-lock me-2"></i>' + plannedBtn.textContent;
                    }
                    if (!unplannedBtn.querySelector('.fas.fa-lock')) {
                        unplannedBtn.innerHTML = '<i class="fas fa-lock me-2"></i>' + unplannedBtn.textContent;
                    }
                    
                    if (!document.querySelector('.alert-warning')) {
                        const warningDiv = document.createElement('div');
                        warningDiv.className = 'alert alert-warning';
                        warningDiv.innerHTML = `
                            <i class="fas fa-exclamation-triangle"></i>
                            В данный момент проводится инвентаризация. Новую инвентаризацию можно будет начать только после завершения текущей.
                            <br>
                            <a href="/inventory/current" class="alert-link">Перейти к текущей инвентаризации</a>
                        `;
                        const headerElement = document.querySelector('.inventory-container h1');
                        if (headerElement) {
                            headerElement.after(warningDiv);
                        }
                    }
                } else {
                    plannedBtn.disabled = false;
                    unplannedBtn.disabled = false;
                    plannedBtn.title = "";
                    unplannedBtn.title = "";
                    plannedBtn.textContent = "Провести плановую инвентаризацию";
                    unplannedBtn.textContent = "Провести внеплановую инвентаризацию";
                    
                    const warning = document.querySelector('.alert-warning');
                    if (warning) {
                        warning.remove();
                    }
                }
            })
            .catch(error => console.error('Error checking inventory status:', error));
    }

    // Проверяем статус при загрузке страницы
    checkInventoryStatus();

    // Проверяем статус каждые 5 секунд
    setInterval(checkInventoryStatus, 5000);

    // Подсветка активного пункта меню
    const currentUrl = window.location.pathname;
    const currentInventoryBtn = document.getElementById('current-inventory-btn');
    const historyInventoryBtn = document.getElementById('history-inventory-btn');
    
    if (currentInventoryBtn && historyInventoryBtn) {
        if (currentUrl.endsWith('/current')) {
            currentInventoryBtn.classList.add('active');
        } else if (currentUrl.endsWith('/history')) {
            historyInventoryBtn.classList.add('active');
        }
    }
    
    // Подсветка активного пункта в навигации
    const navItems = document.querySelectorAll('.nav-link.dropdown-toggle');
    navItems.forEach(item => {
        if (currentUrl.includes('inventory')) {
            if (item.textContent.trim() === 'Инвертаризация') {
                item.style.fontWeight = '600';
            }
        }
    });
}); 