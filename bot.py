from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes

WEBAPP_URL = "https://gulyai-webapp.vercel.app"

from telegram.ext import ApplicationBuilder, CommandHandler

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Добавь свои handlers, например:
    app.add_handler(CommandHandler("start", start))

    await app.run_polling()

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

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())