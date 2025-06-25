// Функция для валидации полей в реальном времени
function validateField(input, regex, errorElement, errorMessage) {
    if (input.value && !regex.test(input.value)) {
        input.classList.add('is-invalid');
        if (errorElement) {
            errorElement.textContent = errorMessage;
        }
        return false;
    } else {
        input.classList.remove('is-invalid');
        return true;
    }
}

// Обработка загрузки фото
document.getElementById('id_photo').addEventListener('change', function(e) {
    var file = e.target.files[0];
    var preview = document.getElementById('photoPreview');
    var container = document.querySelector('.photo-upload-container');
    
    if (file) {
        if (file.size > 5 * 1024 * 1024) {
            alert('Файл больше 5MB');
            this.value = '';
            return;
        }
        
        if (!file.type.match('image/jpeg') && !file.type.match('image/png')) {
            alert('Только JPG и PNG');
            this.value = '';
            return;
        }
        
        var reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            container.classList.add('has-preview');
        }
        reader.readAsDataURL(file);
    } else {
        preview.style.display = 'none';
        container.classList.remove('has-preview');
    }
});

// Обработка drag & drop
var dropZone = document.querySelector('.photo-upload-container');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (eventName === 'dragenter' || eventName === 'dragover') {
            this.classList.add('dragging');
        } else {
            this.classList.remove('dragging');
        }
        
        if (eventName === 'drop') {
            var fileInput = document.getElementById('id_photo');
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
});

// Предотвращаем открытие файла в браузере при drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    document.body.addEventListener(eventName, function(e) {
        e.preventDefault();
        e.stopPropagation();
    });
});

// Валидация полей при вводе
document.getElementById('id_inventory_number').addEventListener('input', function() {
    validateField(
        this,
        /^\d+$/,
        document.getElementById('inventoryNumberError'),
        'Инвентарный номер должен содержать только цифры'
    );
});

document.getElementById('id_book_value').addEventListener('input', function() {
    validateField(
        this,
        /^\d*\.?\d*$/,
        document.getElementById('bookValueError'),
        'Балансовая стоимость должна содержать только цифры и точку'
    );
});

document.getElementById('id_year_of_manufacture').addEventListener('input', function() {
    validateField(
        this,
        /^\d{0,4}$/,
        document.getElementById('yearError'),
        'Год выпуска должен содержать только 4 цифры'
    );
});

document.getElementById('id_responsible').addEventListener('input', function() {
    validateField(
        this,
        /^[a-zA-Zа-яА-ЯёЁ\s\-]*$/,
        document.getElementById('responsibleError'),
        'Поле "Ответственный" должно содержать только буквы, пробелы и тире'
    );
});

// Валидация формы при отправке
document.getElementById('propertyForm').addEventListener('submit', function(e) {
    var inventoryNumber = document.getElementById('id_inventory_number');
    var assetName = document.getElementById('id_asset_name');
    var quantity = document.getElementById('id_quantity');
    var bookValue = document.getElementById('id_book_value');
    var yearOfManufacture = document.getElementById('id_year_of_manufacture');
    var responsible = document.getElementById('id_responsible');
    
    let isValid = true;

    if (!validateField(inventoryNumber, /^\d+$/, document.getElementById('inventoryNumberError'), 'Инвентарный номер должен содержать только цифры')) {
        isValid = false;
    }

    if (!validateField(assetName, /^[a-zA-Zа-яА-ЯёЁ\s\-_.,()]+$/, null, 'Недопустимые символы в наименовании')) {
        isValid = false;
    }

    if (!validateField(quantity, /^[1-9]\d*$/, null, 'Количество должно быть целым положительным числом')) {
        isValid = false;
    }

    if (bookValue.value && !validateField(bookValue, /^\d*\.?\d*$/, document.getElementById('bookValueError'), 'Балансовая стоимость должна содержать только цифры и точку')) {
        isValid = false;
    }

    if (yearOfManufacture.value && !validateField(yearOfManufacture, /^\d{4}$/, document.getElementById('yearError'), 'Год выпуска должен содержать только 4 цифры')) {
        isValid = false;
    }

    if (responsible.value && !validateField(responsible, /^[a-zA-Zа-яА-ЯёЁ\s\-]+$/, document.getElementById('responsibleError'), 'Поле "Ответственный" должно содержать только буквы, пробелы и тире')) {
        isValid = false;
    }

    if (!isValid) {
        e.preventDefault();
    }
}); 