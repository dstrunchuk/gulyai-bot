
import os
import json
import logging
import requests
from dotenv import load_dotenv
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

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "987664835"))
WEBAPP_URL = "https://gulyai-webapp.vercel.app"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

logging.basicConfig(level=logging.INFO)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    intro = (
        "💬 Сегодня сложно познакомиться с кем-то по-настоящему живым и неподдельным."
        "Тиндер, Bumble и другие — это про свидания, алгоритмы и бесконечные свайпы."
        "А что, если тебе просто хочется *погулять*, *выдохнуть*, *поболтать с кем-то*, кто рядом?"
    )
    how_it_works = (
        "\n👣 Как работает Gulyai:\n\n"
        "1️⃣ Заполни анкету — укажи имя, адрес, интересы и т.д.\n"
        "2️⃣ Нажми “Гулять” — увидишь свою анкету.\n"
        "3️⃣ Дополни анкету и жми гулять где увидишь список людей.\n"
    )
    await update.message.reply_text(
        intro + how_it_works,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Далее", callback_data="continue_warning")]
        ])
    )

# ⚠️ После "Далее"
async def handle_continue_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "⚠️ *Внимание!*\nНе встречайтесь в незнакомых местах. Первый запуск может быть долгим.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Гулять", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
    )

# /form — команда
async def form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Хочешь снова заполнить анкету?",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
            resize_keyboard=True
        )
    )

# /admin — только для тебя
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "⚙️ Админка:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Отправить уведомление", callback_data="broadcast")],
            [InlineKeyboardButton("👥 Кол-во анкет", callback_data="count_users")]
        ])
    )

# Обработка нажатий
async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != ADMIN_ID:
        return

    if query.data == "count_users":
        res = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?select=chat_id",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )
        count = len(res.json()) if res.ok else "?"
        await query.message.reply_text(f"👥 Всего анкет: {count}")

    if query.data == "broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.message.reply_text("✍️ Введи текст для рассылки или /cancel")

# Текст от админа
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.user_data.get("awaiting_broadcast"):
        text = update.message.text
        await update.message.reply_text("✅ Рассылаем...")

        res = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?select=chat_id",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )
        if not res.ok:
            await update.message.reply_text("❌ Не удалось получить список.")
            return

        for user in res.json():
            try:
                await context.bot.send_message(chat_id=user["chat_id"], text=text)
            except Exception:
                continue

        await update.message.reply_text("✅ Уведомление отправлено.")
        context.user_data["awaiting_broadcast"] = False

# /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        context.user_data["awaiting_broadcast"] = False
        await update.message.reply_text("❌ Отменено.")

# Запуск
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("form", form))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("cancel", cancel))
app.add_handler(CallbackQueryHandler(handle_continue_warning, pattern="^continue_warning$"))
app.add_handler(CallbackQueryHandler(handle_admin_action, pattern="^(broadcast|count_users)$"))
app.add_handler(MessageHandler(filters.TEXT, handle_text))

print("🤖 Gulyai-бот запущен!")
app.run_polling()
