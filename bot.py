import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Конфигурация
DATA_FILE = "data/feedings.json"
MAX_DAILY = 3
MAX_WEEKLY = 5

class FeedingSystem:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_file = self.data_dir / "feedings.json"
        self._ensure_data_file()
        self.load_data()
    
    def _ensure_data_file(self):
        """Гарантирует существование файла данных"""
        self.data_dir.mkdir(exist_ok=True)
        if not self.data_file.exists():
            self.data = {
                "feedings": [],
                "weekly_reset": self.next_monday()
            }
            self.save_data()
    
    def load_data(self):
        """Загружает данные из файла"""
        try:
            with open(self.data_file, "r", encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"Данные загружены из {self.data_file}")
        except Exception as e:
            print(f"Ошибка загрузки: {e}. Создаю новый файл")
            self.data = {
                "feedings": [],
                "weekly_reset": self.next_monday()
            }
            self.save_data()
    
    def save_data(self):
        """Сохраняет данные в файл"""
        try:
            with open(self.data_file, "w", encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"Данные сохранены в {self.data_file}")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def next_monday(self):
        today = datetime.now()
        return (today + timedelta(days=(7 - today.weekday()))).strftime("%Y-%m-%d")
    
    def check_weekly_reset(self):
        """Сбрасывает данные раз в неделю"""
        if datetime.now().strftime("%Y-%m-%d") >= self.data["weekly_reset"]:
            print("Сброс недельных данных")
            self.data["feedings"] = []
            self.data["weekly_reset"] = self.next_monday()
            self.save_data()
    
    def can_feed_today(self, user_id):
        today = datetime.now().strftime("%Y-%m-%d")
        today_feedings = [f for f in self.data["feedings"] 
                        if f["date"] == today and f["user_id"] == str(user_id)]
        return sum(f["sticks"] for f in today_feedings) < MAX_DAILY
    
    def can_feed_week(self, user_id):
        week_feedings = [f for f in self.data["feedings"] 
                        if f["user_id"] == str(user_id)]
        return sum(f["sticks"] for f in week_feedings) < MAX_WEEKLY
    
    def add_feeding(self, user_id, username, sticks):
        if not self.can_feed_today(user_id):
            return False, "Сегодня уже достигнут лимит кормления (3 палочки)"
        
        if not self.can_feed_week(user_id):
            return False, "На этой неделе уже достигнут лимит кормления (5 палочек)"
        
        feeding = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "user_id": str(user_id),
            "username": username or "Неизвестный",
            "sticks": int(sticks)  # Гарантируем что это число
        }
        
        self.data["feedings"].append(feeding)
        self.save_data()
        return True, f"{username} дал {sticks} палочку(и)"
    
    def get_feedings(self):
        """Возвращает копию данных для безопасности"""
        return list(self.data["feedings"])

feeding_system = FeedingSystem()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для учета кормления рыбок.\n\n"
        "Доступные команды:\n"
        "/feed - Покормить рыбок\n"
        "/history - Кто кормил"
    )

async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    web_app_url = f"https://mishateterin.github.io/fishfeeder/?user_id={user.id}&username={user.username or user.first_name}"
    
    await update.message.reply_text(
        "Нажмите кнопку чтобы покормить рыбок:",
        reply_markup={
            "inline_keyboard": [[{
                "text": "Покормить рыбок",
                "web_app": {"url": web_app_url}
            }]]
        }
    )

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feedings = feeding_system.get_feedings()
    if not feedings:
        await update.message.reply_text("Пока никто не кормил рыбок")
        return
    
    message = "История кормлений:\n\n"
    for f in reversed(feedings[-10:]):  # Показываем последние 10 записей
        message += f"{f['date']} {f['time']} - {f['username']}: {f['sticks']} палочки(и)\n"
    
    await update.message.reply_text(message)

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("Получены сырые данные:", update.message.web_app_data.data) # Логируем
        
        data = json.loads(update.message.web_app_data.data)
        print("Распарсенные данные:", data) # Логируем
        
        if not all(k in data for k in ["user_id", "username", "sticks"]):
            raise ValueError("Не хватает обязательных полей")
            
        success, message = feeding_system.add_feeding(
            str(data["user_id"]),
            str(data["username"]),
            int(data["sticks"])
        )
        print("Результат сохранения:", success, message) # Логируем
        await update.message.reply_text(message)
        
    except Exception as e:
        error_msg = f"Ошибка: {str(e)}"
        print(error_msg) # Логируем
        await update.message.reply_text(error_msg)

if __name__ == "__main__":
    app = Application.builder().token("8191936573:AAFOYto7gQPW1qrnDY7BNrTj3mAZiWYzYFo").build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("feed", feed))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    app.run_polling()