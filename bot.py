import os
import json
import logging
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
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

load_dotenv()

TOKEN = os.getenv("TOKEN")
WEBAPP_URL = "https://gulyai-webapp.vercel.app"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
ADMIN_ID = 987664835

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    intro = (
        "💬 Сегодня сложно познакомиться с кем-то по-настоящему живым и неподдельным.\n\n"
        "Тиндер, Bumble и другие — это про свидания, алгоритмы и бесконечные свайпы.\n\n"
        "А что, если тебе просто хочется *погулять*, *выдохнуть*, *поболтать с кем-то*, кто рядом?\n"
    )

    how = (
        "\n👣 Как работает Gulyai:\n\n"
        "1️⃣ Заполни анкету — укажи имя, адрес, интересы и т.д.\n"
        "2️⃣ Нажми “Гулять” — увидишь свою анкету.\n"
        "3️⃣ Подтверди статус и увидишь список людей рядом."
    )

    buttons = [[InlineKeyboardButton("➡️ Далее", callback_data="continue_warning")]]

    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ Админка", callback_data="admin_menu")])

    await update.message.reply_text(
        intro + how,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Предупреждение
async def handle_continue_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "⚠️ Не встречайтесь в незнакомых районах. Первый запуск может быть долгим.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Гулять", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
    )

# Админка
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "⚙️ Админ-панель",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Сколько анкет", callback_data="count_profiles")],
            [InlineKeyboardButton("✉️ Отправить сообщение", callback_data="broadcast_text")],
            [InlineKeyboardButton("◀️ Назад", callback_data="continue_warning")]
        ])
    )

# Кол-во анкет
async def handle_count_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        result = supabase.table("users").select("chat_id").execute()
        count = len(result.data)
        await query.message.reply_text(f"📊 Всего анкет: {count}")
    except Exception as e:
        await query.message.reply_text(f"Ошибка: {e}")

# Начало рассылки
async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_broadcast"] = True

    await query.message.reply_text("✍️ Введи сообщение для рассылки.\nНапиши *назад*, чтобы отменить.", parse_mode="Markdown")

# Получение текста для рассылки
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get("awaiting_broadcast"):
        text = update.message.text.strip()
        if text.lower() == "назад":
            context.user_data["awaiting_broadcast"] = False
            await update.message.reply_text("↩️ Рассылка отменена.")
            return

        await update.message.reply_text("⏳ Отправляем сообщение...")

        try:
            result = supabase.table("users").select("chat_id").execute()
            count = 0

            for user in result.data:
                chat_id = user["chat_id"]
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": text}
                    )
                    count += 1
                except Exception as e:
                    print(f"❌ Не отправлено пользователю {chat_id}: {e}")

            await update.message.reply_text(f"✅ Сообщение отправлено {count} пользователям.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка при рассылке: {e}")

        context.user_data["awaiting_broadcast"] = False

# /form — повторно заполнить
async def form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Хочешь снова заполнить анкету?",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
            resize_keyboard=True
        )
    )

# Получение анкеты из WebApp
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)

        text = (
            f"📬 Анкета получена!\n\n"
            f"Имя: {data.get('name')}\n"
            f"Адрес: {data.get('address')}\n"
            f"Возраст: {data.get('age')}\n"
            f"Интересы: {data.get('interests')}\n"
            f"Цель: {data.get('activity')}\n"
            f"Настроение: {data.get('vibe')}"
        )

        await update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
                resize_keyboard=True
            )
        )
    except Exception as e:
        logging.error(f"Ошибка обработки анкеты: {e}")
        await update.message.reply_text("❌ Ошибка при обработке анкеты.")

# Запуск
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_continue_warning, pattern="^continue_warning$"))
app.add_handler(CallbackQueryHandler(admin_menu, pattern="^admin_menu$"))
app.add_handler(CallbackQueryHandler(handle_count_profiles, pattern="^count_profiles$"))
app.add_handler(CallbackQueryHandler(handle_broadcast_text, pattern="^broadcast_text$"))
app.add_handler(CommandHandler("form", form))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))
app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), handle_text_message))

print("🤖 Gulyai бот запущен!")
app.run_polling()