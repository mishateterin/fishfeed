document.addEventListener('DOMContentLoaded', () => {
    // Получаем параметры из URL
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('user_id');
    const username = urlParams.get('username');
    
    // Инициализация Telegram WebApp
    if (window.Telegram?.WebApp) {
        Telegram.WebApp.expand();
        Telegram.WebApp.MainButton.setText('Закрыть').show();
        Telegram.WebApp.MainButton.onClick(() => Telegram.WebApp.close());
    }
    
    // Обработка выбора палочек
    document.querySelectorAll('.stick-options button').forEach(button => {
        button.addEventListener('click', () => {
            const sticks = parseInt(button.dataset.sticks);
            feedFish(userId, username, sticks);
        });
    });
});

function feedFish(userId, username, sticks) {
    const statusElement = document.getElementById('status');
    
    // Отправляем данные в бота
    if (window.Telegram?.WebApp) {
        const data = {
            user_id: userId,
            username: username,
            sticks: sticks
        };
        
        Telegram.WebApp.sendData(JSON.stringify(data));
        statusElement.textContent = `Отправлено: ${username} дает ${sticks} палочку(и)`;
        statusElement.className = 'status success';
        
        // Закрываем через 2 секунды
        setTimeout(() => Telegram.WebApp.close(), 2000);
    } else {
        statusElement.textContent = 'Ошибка: приложение должно быть открыто в Telegram';
        statusElement.className = 'status error';
    }
}

function sendFeedingData(sticks) {
    const urlParams = new URLSearchParams(window.location.search);
    const data = {
        user_id: urlParams.get('user_id') || "unknown",
        username: urlParams.get('username') || "Гость",
        sticks: parseInt(sticks)
    };
    
    console.log("Отправка данных в бота:", data); // Логируем
    
    if (window.Telegram?.WebApp) {
        Telegram.WebApp.sendData(JSON.stringify(data));
        Telegram.WebApp.close();
    }
}