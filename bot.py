import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# 🔑 Bot token
BOT_TOKEN2 = "7580086418:AAFRxYUb4bKHonLQge7jIpYF8SBRRPI9tjQ"

# 👑 Owner ID
OWNER_ID2 = 5825048491  # change this to your Telegram ID

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Buy Nothing - 10,000⭐", callback_data="10000")],
        [InlineKeyboardButton("Buy Nothing - 20,000⭐", callback_data="20000")],
        [InlineKeyboardButton("Buy Nothing - 30,000⭐", callback_data="30000")],
        [InlineKeyboardButton("Buy Nothing - 40,000⭐", callback_data="40000")],
        [InlineKeyboardButton("Buy Nothing - 50,000⭐", callback_data="50000")],
        [InlineKeyboardButton("Buy Nothing - 60,000⭐", callback_data="60000")],
        [InlineKeyboardButton("Buy Nothing - 70,000⭐", callback_data="70000")],
        [InlineKeyboardButton("Buy Nothing - 80,000⭐", callback_data="80000")],
        [InlineKeyboardButton("Buy Nothing - 90,000⭐", callback_data="90000")],
        [InlineKeyboardButton("Buy Nothing - 100,000⭐", callback_data="100000")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✨ Welcome to the *Nothing Store* ✨\n\n"
        "Here you can buy absolutely *Nothing*.\n"
        "Because only those who own everything… can afford nothing.\n\n"
        "Choose your Nothing package below:",
        reply_markup=reply_markup
    )

# Handle button presses
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    price = query.data
    user = query.from_user

    message = (
        f"🎉 Congratulations {user.first_name}!\n\n"
        f"You just bought *Nothing* for {price} Stars.\n"
        "Remember: Only those who own everything can afford nothing. 🌀"
    )

    await query.edit_message_text(message)

    # Notify owner (you)
    await context.bot.send_message(
        OWNER_ID2,
        f"📩 User @{user.username or user.id} bought NOTHING for {price} Stars!"
    )

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN2).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is running... (Nothing Store)")
    app.run_polling()

if __name__ == "__main__":
    main()
