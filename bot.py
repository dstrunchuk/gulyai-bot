import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.environ.get("TOKEN")
WEBAPP_URL = "https://gulyai-webapp.vercel.app"

# /start — первый блок
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Как работает Gulyai:\n"
        "1️⃣ Заполни анкету\n"
        "Укажи имя, район, интересы — ничего лишнего. Просто, быстро и по делу.\n\n"
        "2️⃣ Нажми “Готов к встрече”\n"
        "Бот покажет тебе других людей, которые тоже хотят выйти и пообщаться прямо сейчас.\n\n"
        "3️⃣ Связь через Telegram\n"
        "Захотел — написал, договорился, встретился. Никаких лишних платформ."
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("➡️ Далее")]],
            resize_keyboard=True
        )
    )

# После нажатия "Далее" — предупреждение + кнопка WebApp
async def continue_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "➡️ Далее":
        warning = (
            "⚠️ *Внимание!*\n"
            "Не встречайтесь в незнакомых местах, улицах.\n"
            "Гуляйте в более обоюдных местах!"
        )
        await update.message.reply_text(
            warning,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(text="📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
                resize_keyboard=True
            )
        )

# Приём анкеты
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.web_app_data.data
    await update.message.reply_text(f"📬 Анкета получена:\n\n{data}")

# Запуск
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^➡️ Далее$"), continue_flow))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))

print("🤖 Бот запущен. Ждёт команду /start")
app.run_polling()
