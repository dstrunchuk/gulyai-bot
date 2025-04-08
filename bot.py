from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "7512181077:AAFlnJ-gEJMFRbeDX5nO8cOpcErRPPX2vl4"

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Как работает Gulyai:\n"
        "1. Заполни анкету\n"
        "Укажи имя, район, интересы — ничего лишнего. Просто, быстро и по делу.\n\n"
        "2. Нажми “Готов к встрече”\n"
        "Бот покажет тебе других людей, которые тоже хотят выйти и пообщаться прямо сейчас.\n\n"
        "3. Связь через Telegram\n"
        "Захотел — написал, договорился, встретился. Никаких лишних платформ."
    )
    keyboard = [
        [InlineKeyboardButton("Далее", callback_data="next_step")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

# после нажатия "Далее"
async def next_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="⚠️ Внимание! Не встречайтесь в незнакомых вам местах, улицах. Гуляйте в более обоюдных местах!"
    )

# просто запускаем без async/await
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(next_step, pattern="^next_step$"))

    print("Бот запущен... (нажми /start в Telegram)")
    app.run_polling()

if __name__ == '__main__':
    main()
