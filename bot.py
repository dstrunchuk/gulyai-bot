import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

TOKEN = os.environ.get("TOKEN")
WEBAPP_URL = "https://gulyai-webapp.vercel.app"

# /start — первое сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Как работает Gulyai:\n\n"
        "1️⃣ Заполни анкету\n"
        "Укажи имя, район, интересы — ничего лишнего. Просто, быстро и по делу.\n\n"
        "2️⃣ Нажми “Готов к встрече”\n"
        "Бот покажет тебе других людей, которые тоже хотят выйти и пообщаться прямо сейчас.\n\n"
        "3️⃣ Связь через Telegram\n"
        "Захотел — написал, договорился, встретился. Никаких лишних платформ."
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Далее", callback_data="continue_warning")]
        ])
    )

# Нажатие на "Далее"
async def handle_continue_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    warning_text = (
        "⚠️ *Внимание!*\n"
        "Не встречайтесь в незнакомых вам местах, улицах.\n"
        "Гуляйте в более обоюдных местах!"
    )

    await query.message.reply_text(
        warning_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
    )

# Приём анкеты из WebApp
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.web_app_data.data
    await update.message.reply_text(f"📬 Анкета получена:\n\n{data}")

# Старт приложения
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_continue_warning, pattern="^continue_warning$"))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))

print("🤖 Бот запущен и ждёт пользователей!")
app.run_polling()
