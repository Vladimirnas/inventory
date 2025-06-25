document.addEventListener('DOMContentLoaded', function() {
    const dropdownToggles = document.querySelectorAll('.nav-link.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            // Проверяем, не был ли клик на стрелке
            const clickX = e.clientX - toggle.getBoundingClientRect().left;
            if (clickX < toggle.offsetWidth - 20) { 
                window.location.href = this.getAttribute('href');
            }
        });
    });
}); 