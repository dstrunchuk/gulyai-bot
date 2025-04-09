import os
import asyncio
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# 🔐 Получение токена из переменных Railway
TOKEN = os.environ.get("TOKEN")

# 🌐 URL твоего WebApp на Vercel
WEBAPP_URL = "https://gulyai-webapp.vercel.app"

# 📌 Команда /start: приветствие + кнопка
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Как работает Gulyai:\n"
        "1️⃣ Заполни анкету\n"
        "Укажи имя, район, интересы — ничего лишнего. Просто, быстро и по делу.\n\n"
        "2️⃣ Нажми “Готов к встрече”\n"
        "Бот покажет тебе других людей, которые тоже хотят выйти и пообщаться прямо сейчас.\n\n"
        "3️⃣ Связь через Telegram\n"
        "Захотел — написал, договорился, встретился. Никаких лишних платформ.\n\n"
        "⚠️ *Внимание!* Не встречайтесь в незнакомых вам местах, улицах. "
        "Гуляйте в более обоюдных местах!"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(text="📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
            resize_keyboard=True
        )
    )

# 🔁 Приём анкеты из WebApp
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.web_app_data.data
    await update.message.reply_text(f"📬 Анкета получена:\n\n{data}")

# 🚀 Main функция запуска
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))

    print("🤖 Бот запущен. Ожидает команды /start")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
