import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("7675911313:AAGJVySgJ02_vIWIrVa3GbulP4X2Qvl1xbk")  # ✅ теперь безопасно

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Получена команда /start")
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
    await query.edit_message_text(
        text="⚠️ Не встречайтесь в подозрительных местах. Встречайтесь в людных зонах!"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(next_step, pattern="^next_step$"))
    print("Бот работает! ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
