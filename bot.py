import os
import json
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# ✅ Конфигурация
TOKEN = os.environ.get("TOKEN")
WEBAPP_URL = "https://gulyai-webapp.vercel.app"
USERS_FILE = "users.json"

logging.basicConfig(level=logging.INFO)

# 🧠 Хранилище
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_user(user_data):
    users = load_users()
    users.append(user_data)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# 🚀 /start
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

# ⚠️ После "Далее"
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
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
            resize_keyboard=True
        )
    )

# 🔁 /form — повторный вызов
async def form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Хочешь снова заполнить анкету? Нажми кнопку ниже:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
            resize_keyboard=True
        )
    )

# 📥 Прием анкеты
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        save_user(data)
        print("🔥 Пришли данные из WebApp:")
        print(data)

        # ✅ Обновляем ключи
        name = data.get("name", "—")
        district = data.get("location", "—")
        age = data.get("age", "—")
        interests = data.get("interests", "—")
        activity = data.get("activity", "—")
        vibe = data.get("vibe", "—")

        await update.message.reply_text(
            f"📬 Анкета получена!\n\n"
            f"Имя: {name}\n"
            f"Район: {district}\n"
            f"Возраст: {age}\n"
            f"Интересы: {interests}\n"
            f"Цель: {activity}\n"
            f"Настроение: {vibe}",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
                resize_keyboard=True
            )
        )
    except Exception as e:
        logging.error(f"Ошибка обработки анкеты: {e}")
        await update.message.reply_text("❌ Ошибка при обработке анкеты. Попробуйте снова.")

# 🚀 Запуск через polling (надёжно)
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_continue_warning, pattern="^continue_warning$"))
app.add_handler(CommandHandler("form", form))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))

print("🤖 Gulyai готов к приёму анкет!")
app.run_polling()
