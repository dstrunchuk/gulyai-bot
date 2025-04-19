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

TOKEN = os.getenv("TOKEN")
WEBAPP_URL = "https://gulyai-webapp.vercel.app"
USERS_FILE = "users.json"
ADMIN_ID = 987664835  # только твой ID

logging.basicConfig(level=logging.INFO)

# Хранилище
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_user(user_data):
    users = load_users()
    existing = [u for u in users if u["chat_id"] == user_data["chat_id"]]
    if not existing:
        users.append(user_data)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    intro = (
        "💬 Сегодня сложно познакомиться с кем-то по-настоящему живым и неподдельным.\n\n"
        "Тиндер, Bumble и другие — это про свидания, алгоритмы и бесконечные свайпы.\n\n"
        "А что, если тебе просто хочется *погулять*, *выдохнуть*, *поболтать с кем-то*, кто рядом?\n"
    )

    how_it_works = (
        "\n👣 Как работает Gulyai:\n\n"
        "1️⃣ Заполни анкету — укажи имя, адрес, интересы и т.д.\n"
        "2️⃣ Нажми “Гулять” — увидишь свою анкету.\n"
        "3️⃣ Дополни анкету и жми гулять, где увидишь список людей.\n"
    )

    buttons = [
        [InlineKeyboardButton("➡️ Далее", callback_data="continue_warning")]
    ]

    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ Админка", callback_data="admin_menu")])

    await update.message.reply_text(
        intro + how_it_works,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Предупреждение
async def handle_continue_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "⚠️ *Внимание!*\nНе встречайтесь в незнакомых улицах. Гуляйте в людных местах.\n\n"
        "Первый запуск приложения может быть долгим",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Гулять", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
    )

# Повтор анкеты
async def form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Хочешь снова заполнить анкету? Нажми кнопку ниже:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
            resize_keyboard=True
        )
    )

# Анкета из WebApp
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        data["chat_id"] = update.effective_user.id
        save_user(data)

        text = (
            f"📬 Анкета получена!\n\n"
            f"Имя: {data.get('name', '—')}\n"
            f"Адрес: {data.get('address', '—')}\n"
            f"Возраст: {data.get('age', '—')}\n"
            f"Интересы: {data.get('interests', '—')}\n"
            f"Цель: {data.get('activity', '—')}\n"
            f"Настроение: {data.get('vibe', '—')}"
        )

        await update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
                resize_keyboard=True
            )
        )
    except Exception as e:
        logging.error(f"❌ Ошибка анкеты: {e}")
        await update.message.reply_text("Произошла ошибка при обработке анкеты. Попробуй снова.")

# Админка
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "⚙️ Админка — выбери действие:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📨 Отправить сообщение всем", callback_data="broadcast")],
            [InlineKeyboardButton("📊 Кол-во анкет", callback_data="count_users")],
        ])
    )

# Броадкаст
async def handle_broadcast_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["broadcast_mode"] = True

    await query.message.reply_text(
        "✍️ Напиши текст, который отправить всем пользователям.\n\n❌ Чтобы отменить — просто ничего не пиши."
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("broadcast_mode"):
        context.user_data["broadcast_mode"] = False
        message = update.message.text
        users = load_users()

        success, failed = 0, 0
        for u in users:
            try:
                await context.bot.send_message(chat_id=u["chat_id"], text=message)
                success += 1
            except:
                failed += 1

        await update.message.reply_text(
            f"✅ Сообщение отправлено {success} пользователям.\n❌ Не удалось отправить: {failed}"
        )

# Подсчёт анкет
async def handle_user_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(f"📊 Всего анкет: {len(users)}")

# Запуск
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_continue_warning, pattern="^continue_warning$"))
app.add_handler(CallbackQueryHandler(admin_menu, pattern="^admin_menu$"))
app.add_handler(CallbackQueryHandler(handle_broadcast_request, pattern="^broadcast$"))
app.add_handler(CallbackQueryHandler(handle_user_count, pattern="^count_users$"))
app.add_handler(CommandHandler("form", form))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))
app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), handle_text_message))

print("🤖 Gulyai бот запущен!")
app.run_polling()