document.addEventListener('DOMContentLoaded', function() {
    // Обработчик для кнопки создания QR-кода
    document.getElementById('saveLocationBtn').addEventListener('click', function() {
        const locationName = document.getElementById('locationName').value.trim();
        if (locationName) {
            createLocationQR(locationName);
        } else {
            alert('Введите название помещения');
        }
    });
    
    // Обработчики для кнопок просмотра оборудования
    document.querySelectorAll('.view-equipment').forEach(button => {
        button.addEventListener('click', function() {
            const locationId = this.getAttribute('data-location-id');
            const locationName = this.getAttribute('data-location-name');
            fetchEquipment(locationId, locationName);
        });
    });
    
    // Обработчики для кнопок скачивания QR-кода
    document.querySelectorAll('.download-qr').forEach(button => {
        button.addEventListener('click', function() {
            const qrSrc = this.getAttribute('data-qr-src');
            const locationName = this.getAttribute('data-location-name');
            downloadQR(qrSrc, locationName);
        });
    });

    // Обработчики для кнопок удаления
    document.querySelectorAll('.delete-location-btn').forEach(button => {
        button.addEventListener('click', function() {
            const locationId = this.getAttribute('data-location-id');
            const locationName = this.getAttribute('data-location-name');
            deleteLocation(locationId, locationName);
        });
    });

    // Обработка чекбоксов для печати
    const checkboxes = document.querySelectorAll('.print-checkbox');
    const printSelectedBtn = document.getElementById('printSelectedBtn');
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updatePrintButton);
    });
    
    function updatePrintButton() {
        const checkedBoxes = document.querySelectorAll('.print-checkbox:checked');
        printSelectedBtn.disabled = checkedBoxes.length === 0;
    }
    
    // Печать выбранных QR-кодов
    printSelectedBtn.addEventListener('click', function() {
        const checkedBoxes = document.querySelectorAll('.print-checkbox:checked');
        const selectedIds = Array.from(checkedBoxes).map(box => box.dataset.locationId);
        
        if (selectedIds.length > 0) {
            window.open(`/location-qr/print?ids=${selectedIds.join(',')}`, '_blank');
        }
    });
    
    // Печать всех QR-кодов
    document.getElementById('printAllBtn').addEventListener('click', function() {
        window.open('/location-qr/print', '_blank');
    });
    
    // Скачать PDF со всеми QR-кодами
    document.getElementById('downloadPdfBtn').addEventListener('click', function() {
        window.location.href = '/location-qr/print?format=pdf';
    });
});

// Функция для создания QR-кода
function createLocationQR(locationName) {
    fetch('/api/location-qr', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            locationName: locationName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            // Перезагружаем страницу для отображения нового QR-кода
            window.location.reload();
        } else {
            alert('Ошибка при создании QR-кода: ' + (data.error || 'Неизвестная ошибка'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при создании QR-кода');
    });
}

// Функция для получения списка оборудования
function fetchEquipment(locationId, locationName) {
    fetch(`/api/location-qr/equipment/${locationId}`)
        .then(response => response.json())
        .then(data => {
            const equipmentList = document.getElementById('equipmentList');
            document.getElementById('equipmentModalLabel').textContent = `Оборудование в помещении "${locationName}"`;
            
            if (data.length === 0) {
                equipmentList.innerHTML = '<div class="alert alert-info">В этом помещении нет оборудования</div>';
            } else {
                let html = '<table class="table table-striped">';
                html += '<thead><tr><th>Инв. номер</th><th>Наименование</th><th>Ответственный</th><th>Подразделение</th></tr></thead>';
                html += '<tbody>';
                data.forEach(item => {
                    html += `<tr>
                        <td>${item.inventory_number}</td>
                        <td>${item.asset_name}</td>
                        <td>${item.responsible || '-'}</td>
                        <td>${item.department_name || '-'}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                equipmentList.innerHTML = html;
            }
            
            const equipmentModal = new bootstrap.Modal(document.getElementById('equipmentModal'));
            equipmentModal.show();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при получении списка оборудования');
        });
}

// Функция для скачивания QR-кода
function downloadQR(qrSrc, locationName) {
    const link = document.createElement('a');
    link.href = qrSrc;
    link.download = `QR_${locationName.replace(/\s+/g, '_')}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Функция для показа модального окна подтверждения удаления
function deleteLocation(locationId, locationName) {
    document.getElementById('locationNameToDelete').textContent = locationName;
    
    // Настраиваем обработчик кнопки подтверждения
    document.getElementById('confirmDeleteBtn').onclick = function() {
        confirmDeleteLocation(locationId);
    };
    
    // Показываем модальное окно
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    deleteModal.show();
}

// Функция для удаления QR-кода помещения
function confirmDeleteLocation(locationId) {
    fetch(`/api/location-qr/${locationId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Скрываем модальное окно
            bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal')).hide();
            
            // Удаляем карточку с QR-кодом
            const locationCard = document.getElementById(`location-card-${locationId}`);
            if (locationCard) {
                locationCard.remove();
            }
            
            // Если это была последняя карточка, показываем пустое состояние
            if (document.querySelectorAll('.qr-card').length === 0) {
                const container = document.querySelector('.qr-container');
                const row = document.querySelector('.row');
                if (row) {
                    row.remove();
                    
                    const emptyState = document.createElement('div');
                    emptyState.className = 'empty-state';
                    emptyState.innerHTML = `
                        <i class="bi bi-building"></i>
                        <h3>Нет QR-кодов помещений</h3>
                        <p>Создайте новый QR-код для помещения, чтобы начать учет оборудования по местам.</p>
                    `;
                    container.appendChild(emptyState);
                }
            }
            
            // Показываем уведомление об успешном удалении
            alert(data.message);
        } else {
            alert('Ошибка при удалении: ' + (data.error || 'Неизвестная ошибка'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при удалении QR-кода');
    });
} 