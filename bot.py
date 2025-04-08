import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: переменная TOKEN не найдена")
    exit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ Получен /start")
    text = (
        "Как работает Gulyai:\n"
        "1. Заполни анкету\n"
        "2. Нажми 'Готов к встрече'\n"
        "3. Общайся с другими прямо сейчас."
    )
    keyboard = [[InlineKeyboardButton("Далее", callback_data="next_step")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def next_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚠️ Внимание: гуляйте только в безопасных местах!")

def main():
    print(f"📦 Токен получен: {TOKEN[:5]}...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(next_step, pattern="^next_step$"))
    print("🚀 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
