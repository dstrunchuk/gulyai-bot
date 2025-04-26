import os
import json
import logging
import requests
import httpx
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
from fastapi import BackgroundTasks
from fastapi import FastAPI, Request
import asyncio

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

if os.getenv("RUN_ENV") != "production":
    print("Бот работает только на Railway. Запуск остановлен.")
    exit()

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
        reply_markup=ReplyKeyboardMarkup(
            [
                [KeyboardButton("➡️ Далее")],
                [KeyboardButton("🔄 Обновить экран")]
            ],
            resize_keyboard=True
        )
    )
async def handle_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔄 Обновлено! Нажми ➡️ Далее, чтобы продолжить.",
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
    "Не выключайте уведомления!\n\n"
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

            async def send_message(chat_id):
                nonlocal count
                try:
                    await context.bot.send_message(chat_id=chat_id, text=text)
                    count += 1
                except Exception as e:
                    print(f"❌ Не удалось отправить сообщение {chat_id}: {e}")

            tasks = [send_message(user["chat_id"]) for user in users]
            
            # Ограничим до 30 сообщений в секунду
            for i in range(0, len(tasks), 30):
                await asyncio.gather(*tasks[i:i+30])
                await asyncio.sleep(1)

            await query.message.reply_text(f"✅ Рассылка отправлена {count} пользователям.")
        except Exception as e:
            await query.message.reply_text(f"Ошибка при рассылке: {e}")
        finally:
            context.user_data["pending_text"] = None

    elif query.data == "cancel_broadcast":
        context.user_data["pending_text"] = None
        await query.message.reply_text("❌ Рассылка отменена.")

async def handle_meet_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    from_id = data.split("_")[1]

    if data.startswith("agree_"):
        try:
            initiator = await context.bot.get_chat(int(from_id))
            await query.message.reply_text(
                f"✅ Вы согласились! Вот ссылка: [@{initiator.username}](https://t.me/{initiator.username})",
                parse_mode="Markdown"
            )
        except Exception as e:
            print("Ошибка при получении username инициатора:", e)
            await query.message.reply_text(
                f"✅ Вы согласились! Вот ссылка: [Профиль](https://t.me/user?id={from_id})",
                parse_mode="Markdown"
            )
        try:
            await context.bot.send_message(
                chat_id=from_id,
                text=f"✅ {query.from_user.first_name} тоже хочет встретиться с тобой!\n[Открыть профиль](https://t.me/{query.from_user.username})",
                parse_mode="Markdown"
            )

            ADMIN_ID = 987664835  # замени на свой ID
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"👥 {query.from_user.first_name} и пользователь {from_id} согласились встретиться!"
            )

        except Exception as e:
            print("Ошибка при уведомлении отправителя:", e)

    elif data.startswith("decline_"):
        await query.message.reply_text("❌ Вы отклонили предложение.")
        await query.message.reply_text(
            "ℹ️ После отказа ты больше не отображаешься среди активных пользователей. Чтобы снова появиться в списке, нажми «Гулять» в приложении."
        )
        
        # --> Уведомляем инициатора об отказе
        try:
            await context.bot.send_message(
                chat_id=from_id,
                text="❌ Ваше предложение о встрече было отклонено."
            )
        except Exception as e:
            print(f"Ошибка при уведомлении об отказе: {e}")
        
        # --> Статус переводим в offline
        try:
            await httpx.post(
                "https://gulyai-backend-production.up.railway.app/api/set-offline",
                json={"chat_id": query.from_user.id}
            )
        except Exception as e:
            print(f"Ошибка при обновлении статуса через backend: {e}")
        
# Инициализация
bot_app = ApplicationBuilder().token(TOKEN).build()
# Заменяем всё, что после добавления всех handlers:

bot_app = ApplicationBuilder().token(TOKEN).build()
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("form", form))
bot_app.add_handler(CommandHandler("admin", admin_panel))
bot_app.add_handler(CallbackQueryHandler(handle_continue_warning, pattern="^continue_warning$"))
bot_app.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="^admin_"))
bot_app.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^(confirm|cancel)_broadcast$"))
bot_app.add_handler(CallbackQueryHandler(handle_meet_response, pattern="^(agree_|decline_)"))
bot_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), handle_text_message))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🔄 Обновить экран"), handle_refresh))

print("🤖 Бот запущен!")

# FastAPI сервер
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await bot_app.initialize()
    print("✅ Bot initialized")

@app.post(f"/webhook/{TOKEN}")
async def webhook_handler(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        asyncio.create_task(bot_app.process_update(update))  # запускаем в фоне
        print(f"✅ Принято обновление: {data}")
        return {"ok": True}  # сразу ответить Telegram
    except Exception as e:
        print(f"❌ Ошибка обработки webhook: {e}")
        return {"ok": False, "error": str(e)}

# Чтобы Railway нашёл приложение
fastapi_app = app