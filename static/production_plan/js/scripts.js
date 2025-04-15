// Пример функции для обработки события клика
document.addEventListener('DOMContentLoaded', function() {
    console.log('Документ загружен');

    // Пример обработки кнопки
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            console.log('Кнопка нажата');
        });
    });
});
