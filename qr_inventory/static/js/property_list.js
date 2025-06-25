document.addEventListener('DOMContentLoaded', function() {
    // Обработка выбора всех элементов
    const selectAllCheckbox = document.getElementById('selectAll');
    const itemCheckboxes = document.querySelectorAll('.select-item');
    const printSelectedBtn = document.getElementById('printSelectedBtn');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            updatePrintButton();
        });
    }
    
    // Обработка выбора отдельных элементов
    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updatePrintButton);
    });
    
    // Обновление состояния кнопки печати
    function updatePrintButton() {
        const checkedItems = document.querySelectorAll('.select-item:checked');
        
        if (checkedItems.length > 0) {
            printSelectedBtn.disabled = false;
            const selectedIds = Array.from(checkedItems).map(item => item.dataset.id);
            printSelectedBtn.onclick = function() {
                window.open(`/print-asset-qr-codes/?ids=${selectedIds.join(',')}`, '_blank');
                return false;
            };
        } else {
            printSelectedBtn.disabled = true;
        }
        
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = (checkedItems.length === itemCheckboxes.length && itemCheckboxes.length > 0);
        }
    }

    // Функционал сортировки
    const sortableHeaders = document.querySelectorAll('th[data-sort]');
    
    // Получаем текущие параметры сортировки из URL
    const urlParams = new URLSearchParams(window.location.search);
    const currentSort = {
        column: urlParams.get('sort') || null,
        direction: urlParams.get('direction') || 'asc'
    };

    // Устанавливаем начальное состояние иконок сортировки
    updateSortIcons();

    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.sort;
            
            // Определяем направление сортировки
            let direction = 'asc';
            if (currentSort.column === column) {
                direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            }

            // Обновляем URL с параметрами сортировки
            const newParams = new URLSearchParams(window.location.search);
            newParams.set('sort', column);
            newParams.set('direction', direction);
            
            // Сохраняем все существующие параметры
            for (const [key, value] of urlParams.entries()) {
                if (key !== 'sort' && key !== 'direction') {
                    newParams.set(key, value);
                }
            }

            // Перенаправляем на новый URL с параметрами сортировки
            window.location.href = `${window.location.pathname}?${newParams.toString()}`;
        });
    });

    // Функция обновления иконок сортировки
    function updateSortIcons() {
        sortableHeaders.forEach(header => {
            const upIcon = header.querySelector('.sort-up');
            const downIcon = header.querySelector('.sort-down');
            
            if (header.dataset.sort === currentSort.column) {
                if (currentSort.direction === 'asc') {
                    upIcon.classList.add('active');
                    downIcon.classList.remove('active');
                } else {
                    downIcon.classList.add('active');
                    upIcon.classList.remove('active');
                }
            } else {
                upIcon.classList.remove('active');
                downIcon.classList.remove('active');
            }
        });
    }
}); 