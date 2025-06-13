// Основная функция, которая выполняется после полной загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('Документ загружен');

    // Инициализация всех всплывающих подсказок Bootstrap на странице
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Добавляем обработчики клика на все кнопки с классом .btn
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            console.log('Кнопка нажата:', this.textContent.trim());
        });
    });

    // Функция анимации карточек при прокрутке страницы
    const animateOnScroll = function() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            const cardPosition = card.getBoundingClientRect().top; // Позиция карточки относительно видимой части окна
            const screenPosition = window.innerHeight / 1.3;       // Точка срабатывания анимации (примерно 77% высоты экрана)

            if (cardPosition < screenPosition) {
                // Если карточка видна достаточно высоко, применяем анимацию появления
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    };

    // Инициализация начальных стилей для всех карточек (прозрачность и смещение вниз)
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease';
    });

    // Запускаем анимацию при загрузке страницы и при прокрутке
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll();
});

// Функция подтверждения удаления всех активных заданий
function confirmClearAssignments(deleteUrl, csrfToken) {
    if (confirm('Удалить ВСЕ активные задания? Действие нельзя отменить!')) {
        // Создаём форму для отправки POST-запроса с CSRF-токеном
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = deleteUrl;
        form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">`;
        document.body.appendChild(form);
        form.submit();
    }
}

// Обработчик для иконки сворачивания/разворачивания активных и выполненных заданий
document.addEventListener('DOMContentLoaded', function() {
    // Активные задания
    const toggleActiveBtn = document.getElementById('toggleActiveBtn');
    const iconActive = document.getElementById('iconActive');
    const activeCollapse = document.getElementById('active-assignments');

    toggleActiveBtn.addEventListener('click', function() {
        // Задержка нужна, чтобы дождаться завершения анимации Bootstrap Collapse
        setTimeout(() => {
            if (activeCollapse.classList.contains('show')) {
                // Если блок развернут — показываем стрелку вверх
                iconActive.classList.remove('bi-chevron-down');
                iconActive.classList.add('bi-chevron-up');
            } else {
                // Если свернут — стрелка вниз
                iconActive.classList.remove('bi-chevron-up');
                iconActive.classList.add('bi-chevron-down');
            }
        }, 200);
    });

    // Выполненные задания
    const toggleCompletedBtn = document.getElementById('toggleCompletedBtn');
    const iconCompleted = document.getElementById('iconCompleted');
    const completedCollapse = document.getElementById('completed-assignments');

    toggleCompletedBtn.addEventListener('click', function() {
        setTimeout(() => {
            if (completedCollapse.classList.contains('show')) {
                iconCompleted.classList.remove('bi-chevron-down');
                iconCompleted.classList.add('bi-chevron-up');
            } else {
                iconCompleted.classList.remove('bi-chevron-up');
                iconCompleted.classList.add('bi-chevron-down');
            }
        }, 200);
    });
});

// Фильтры для сменных заданий
document.addEventListener('DOMContentLoaded', function () {
        const collapseElement = document.getElementById('filtersCollapse');
        const toggleButton = collapseElement.previousElementSibling.querySelector('button');
        const toggleIcon = document.getElementById('filtersToggleIcon').querySelector('i');

        collapseElement.addEventListener('show.bs.collapse', function () {
            toggleIcon.classList.remove('bi-chevron-down');
            toggleIcon.classList.add('bi-chevron-up');
        });

        collapseElement.addEventListener('hide.bs.collapse', function () {
            toggleIcon.classList.remove('bi-chevron-up');
            toggleIcon.classList.add('bi-chevron-down');
        });
    });

function updateProgress() {
    fetch('/api/production-plans/progress/')
        .then(response => response.json())
        .then(data => {
            data.forEach(plan => {
                // Обновляем прогресс в карточках планов
                const planProgress = document.querySelector(`.card[data-plan-id="${plan.id}"] .progress-bar`);
                if (planProgress) {
                    planProgress.style.width = `${plan.progress}%`;
                    planProgress.setAttribute('aria-valuenow', plan.progress);
                    planProgress.textContent = `${plan.progress}%`;
                    // Обновляем классы цвета
                    planProgress.classList.remove('bg-success', 'bg-warning', 'bg-danger');
                    if (plan.progress < 30) planProgress.classList.add('bg-danger');
                    else if (plan.progress < 70) planProgress.classList.add('bg-warning');
                    else planProgress.classList.add('bg-success');
                }

                // Обновляем прогресс в техкартах (если открыты)
                const techcardProgress = document.querySelector(`.techcard[data-plan-id="${plan.id}"] .progress-bar`);
                if (techcardProgress) {
                    techcardProgress.style.width = `${plan.progress}%`;
                    techcardProgress.setAttribute('aria-valuenow', plan.progress);
                }
            });
        });
}

// Отображение имени выбранного файла
document.getElementById('id_drawing').addEventListener('change', function(e) {
    var fileName = e.target.files[0]?.name || 'Выберите файл...';
    document.querySelector('.custom-file-label').textContent = fileName;
});

// Валидация формы
(function() {
    'use strict';
    window.addEventListener('load', function() {
        var forms = document.getElementsByClassName('needs-validation');
        Array.prototype.filter.call(forms, function(form) {
            form.addEventListener('submit', function(event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();

// Обновляем каждые 30 секунд
setInterval(updateProgress, 300000);
document.addEventListener('DOMContentLoaded', updateProgress);