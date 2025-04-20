import os
import json
import logging
import requests
from postgrest import PostgrestClient
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
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
WEBAPP_URL = "https://gulyai-webapp.vercel.app"
ADMIN_ID = 987664835

db = PostgrestClient(f"{SUPABASE_URL}/rest/v1")
db.session.headers["apikey"] = SUPABASE_KEY
db.session.headers["Authorization"] = f"Bearer {SUPABASE_KEY}"

logging.basicConfig(level=logging.INFO)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Только первый вызов стартуем
    if context.chat_data.get("start_done"):
        return
    context.chat_data["start_done"] = True

    intro = (
        "💬 Сегодня сложно познакомиться с кем-то по-настоящему живым и неподдельным.\n\n"
        "Тиндер, Bumble и другие — это про свидания, алгоритмы и бесконечные свайпы.\n\n"
        "А что, если тебе просто хочется погулять, выдохнуть, поболтать с кем-то, кто рядом?\n\n"
        "👣 Как работает Gulyai:\n\n"
        "1️⃣ Заполни анкету — укажи имя, адрес, интересы и т.д.\n"
        "2️⃣ Нажми “Гулять” — увидишь свою анкету.\n"
        "3️⃣ Дополни анкету и жми гулять где увидишь список людей."
    )

    await update.message.reply_text(
        intro,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Далее", callback_data="continue_warning")]
        ])
    )

# Предупреждение
async def handle_continue_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
    "⚠️ Внимание!\n\n"
    "Не встречайтесь на незнакомых улицах!\n"
    "Гуляйте в более людных местах.",
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Гулять", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
)

# /form
async def form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Хочешь снова заполнить анкету?",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📝 Заполнить анкету", web_app=WebAppInfo(url=WEBAPP_URL))]],
            resize_keyboard=True
        )
    )

# Обработка анкеты
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        name = data.get("name", "—")
        address = data.get("address", "—")

        text = (
            f"📬 Анкета получена!\n\n"
            f"Имя: {name}\n"
            f"Адрес: {address}"
        )

        await update.message.reply_text(text)
    except Exception as e:
        logging.error(f"❌ Ошибка анкеты: {e}")
        await update.message.reply_text("Ошибка при обработке анкеты.")

# Админка
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "⚙️ Админка:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📨 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 Кол-во анкет", callback_data="admin_count")]
        ])
    )

# Обработка админ-кнопок
async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_broadcast":
        context.user_data["awaiting_broadcast"] = True
        context.user_data["pending_text"] = None

        await query.message.reply_text(
            "✍️ Напиши текст рассылки.\n\nЕсли передумал — нажми «Отмена»:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_broadcast")]
            ])
        )

    elif query.data == "admin_count":
        try:
            users = await db.from_("users").select("chat_id").execute()
            count = len(users.data)
            await query.message.reply_text(f"📊 В базе сейчас {count} анкет.")
        except Exception as e:
            await query.message.reply_text(f"Ошибка при получении анкет: {e}")

# Подтверждение рассылки
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_broadcast") and update.effective_user.id == ADMIN_ID:
        context.user_data["awaiting_broadcast"] = False
        context.user_data["pending_text"] = update.message.text

        await update.message.reply_text(
            f"🔒 Подтверди отправку:\n\n{update.message.text}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Отправить", callback_data="confirm_broadcast")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_broadcast")]
            ])
        )

# Подтверждение / отмена
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_broadcast":
        text = context.user_data.get("pending_text", "")
        try:
            result = await db.from_("users").select("chat_id").execute()
            users = result.data
            count = 0
            for user in users:
                chat_id = user["chat_id"]
                try:
                    await context.bot.send_message(chat_id=chat_id, text=text)
                    count += 1
                except Exception as e:
                    print(f"❌ Не удалось отправить сообщение {chat_id}: {e}")
                    continue
            await query.message.reply_text(f"✅ Рассылка отправлена {count} пользователям.")
        except Exception as e:
            await query.message.reply_text(f"Ошибка при рассылке: {e}")
        finally:
            context.user_data["pending_text"] = None

    elif query.data == "cancel_broadcast":
        context.user_data["pending_text"] = None
        await query.message.reply_text("❌ Рассылка отменена.")

# Инициализация
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("form", form))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(handle_continue_warning, pattern="^continue_warning$"))
app.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="^admin_"))
app.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^(confirm|cancel)_broadcast$"))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))
app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), handle_text_message))

print("🤖 Бот запущен!")
app.run_polling()