import os
import json
from datetime import datetime, timedelta
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Конфигурация
DATA_FILE = "data/feedings.json"
MAX_DAILY = 3
MAX_WEEKLY = 5

class FeedingSystem:
    def __init__(self):
        self.load_data()
    
    def load_data(self):
        if not os.path.exists(DATA_FILE):
            self.data = {"feedings": [], "weekly_reset": self.next_monday()}
            self.save_data()
        else:
            with open(DATA_FILE, "r") as f:
                self.data = json.load(f)
            self.check_weekly_reset()
    
    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def next_monday(self):
        today = datetime.now()
        return (today + timedelta(days=(7 - today.weekday())))\
            .strftime("%Y-%m-%d")
    
    def check_weekly_reset(self):
        if datetime.now().strftime("%Y-%m-%d") >= self.data["weekly_reset"]:
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
            "username": username,
            "sticks": sticks
        }
        
        self.data["feedings"].append(feeding)
        self.save_data()
        return True, f"{username} дал {sticks} палочку(и)"
    
    def get_feedings(self):
        return self.data["feedings"]

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
    web_app_url = f"https://mishateterin.github.io/fishfeeder//feed?user_id={user.id}&username={user.username or user.first_name}"
    
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
    data = json.loads(update.message.web_app_data.data)
    user_id = data["user_id"]
    username = data["username"]
    sticks = data["sticks"]
    
    success, message = feeding_system.add_feeding(user_id, username, sticks)
    await update.message.reply_text(message)

if __name__ == "__main__":
    app = Application.builder().token("8191936573:AAFOYto7gQPW1qrnDY7BNrTj3mAZiWYzYFo").build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("feed", feed))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    app.run_polling()