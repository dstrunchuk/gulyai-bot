import os
import json
import logging
import requests
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

TOKEN = os.environ.get("TOKEN")
WEBAPP_URL = "https://gulyai-webapp.vercel.app"
USERS_FILE = "users.json"
BACKEND_API = "https://gulyai-backend-production.up.railway.app/api/text"
ADMIN_ID = 987664835

logging.basicConfig(level=logging.INFO)


# Хранилище
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


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    intro = (
        "💬 Сегодня сложно познакомиться с кем-то по-настоящему живым и неподдельным.\n\n"
        "Тиндер, Bumble и другие — это про свидания, алгоритмы и бесконечные свайпы.\n\n"
        "А что, если тебе просто хочется *погулять*, *выдохнуть*, *поболтать с кем-то*, кто рядом?\n"
    )

    how_it_works = (
        "\n👣 Как работает Gulyai:\n\n"
        "1️⃣ Заполни анкету — укажи имя, адрес, интересы и т.д.\n"
        "2️⃣ Нажми “Гулять” — увидишь свою анкету.\n"
        "3️⃣ Дополни анкету и жми гулять где увидишь список людей.\n"
    )

    buttons = [
        [InlineKeyboardButton("➡️ Далее", callback_data="continue_warning")]
    ]

    # Админ-кнопка
    if update.effective_user.id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ Админка", callback_data="admin_panel")])

    await update.message.reply_text(
        intro + how_it_works,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# После "Далее"
async def handle_continue_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    warning_text = (
        "⚠️ *Внимание!*\n"
        "Не встречайтесь в незнакомых вам улицах.\n"
        "Гуляйте в более людных местах!\n"
        "Первый запуск приложения может быть долгим"
    )

    await query.message.reply_text(
        warning_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Гулять", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
    )


# /form
async def form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Хочешь снова заполнить анкету? Нажми кнопку ниже:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
            resize_keyboard=True
        )
    )


# Получение анкеты
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        save_user(data)

        name = data.get("name", "—")
        address = data.get("address", "—")
        age = data.get("age", "—")
        interests = data.get("interests", "—")
        activity = data.get("activity", "—")
        vibe = data.get("vibe", "—")

        text = (
            f"📬 Анкета получена!\n\n"
            f"Имя: {name}\n"
            f"Адрес: {address}\n"
            f"Возраст: {age}\n"
            f"Интересы: {interests}\n"
            f"Цель: {activity}\n"
            f"Настроение: {vibe}"
        )

        await update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
                resize_keyboard=True
            )
        )

    except Exception as e:
        logging.error(f"❌ Ошибка обработки анкеты: {e}")
        await update.message.reply_text("Произошла ошибка при обработке анкеты. Попробуй снова.")


# Админка
async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("⛔ Доступ запрещён.")
        return

    await query.message.reply_text(
        "⚙️ Админ панель\n\nОтправь текст, который нужно разослать всем пользователям:",
    )
    context.user_data["awaiting_broadcast"] = True


# Обработка текста для рассылки
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_broadcast") and update.effective_user.id == ADMIN_ID:
        text = update.message.text
        response = requests.post(BACKEND_API, json={"text": text})

        if response.status_code == 200:
            await update.message.reply_text("✅ Уведомление разослано!")
        else:
            await update.message.reply_text("❌ Ошибка отправки.")
        context.user_data["awaiting_broadcast"] = False


# Запуск
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_continue_warning, pattern="^continue_warning$"))
app.add_handler(CallbackQueryHandler(handle_admin_panel, pattern="^admin_panel$"))
app.add_handler(CommandHandler("form", form))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("🤖 Gulyai бот с админкой запущен!")
app.run_polling()