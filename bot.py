import logging
import json
import os
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    ContextTypes,
    filters
)

# ============= Settings =============
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # Keep as original
PRICE = 1
PRODUCT_TITLE = "Buy Nothing"
PRODUCT_DESCRIPTION = "Buying literally nothing"
PAYLOAD = "buy_nothing"
PROVIDER_TOKEN = ""  # Keep as original
ORDERS_FILE = "orders.json"

# ============= Logging =============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= Load Orders =============
orders = {}
try:
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            orders = json.load(f)
except json.JSONDecodeError:
    orders = {}

def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

# ============= Main Menu =============
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💎 Buy Nothing", callback_data="buy_menu")],
        [InlineKeyboardButton("📋 My Info", callback_data="my_info")],
        [InlineKeyboardButton("📞 Contact", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============= Commands =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Nothing Shop!\n\n"
        "Choose from the menu:",
        reply_markup=main_menu()
    )

# ============= Button Handler =============
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == "buy_menu":
        keyboard = [
            [InlineKeyboardButton("10,000 ⭐", callback_data="10000")],
            [InlineKeyboardButton("20,000 ⭐", callback_data="20000")],
            [InlineKeyboardButton("30,000 ⭐", callback_data="30000")],
            [InlineKeyboardButton("40,000 ⭐", callback_data="40000")],
            [InlineKeyboardButton("50,000 ⭐", callback_data="50000")],
            [InlineKeyboardButton("60,000 ⭐", callback_data="60000")],
            [InlineKeyboardButton("70,000 ⭐", callback_data="70000")],
            [InlineKeyboardButton("80,000 ⭐", callback_data="80000")],
            [InlineKeyboardButton("90,000 ⭐", callback_data="90000")],
            [InlineKeyboardButton("100,000 ⭐", callback_data="100000")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
        ]
        await query.edit_message_text("Select your Nothing price:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["10000","20000","30000","40000","50000","60000","70000","80000","90000","100000"]:
        await query.edit_message_text(
            f"🎉 Congratulations {query.from_user.first_name}!\n"
            f"You just bought *Nothing* for {query.data} Stars.\n"
            "Only those who own everything can afford nothing. 🌀",
            parse_mode="Markdown"
        )
        # Notify admin as in original
        await context.bot.send_message(
            ADMIN_ID,
            f"📢 User @{query.from_user.username or user_id} bought NOTHING for {query.data} Stars!"
        )

    elif query.data == "my_info":
        order = orders.get(user_id)
        if not order:
            msg = "❌ You have no previous orders."
        else:
            msg = (f"📋 Last order:\n"
                   f"🕒 Time: {order.get('time','-')}\n"
                   f"🎮 Free Fire ID: {order.get('freefire_id','❌ Not sent')}\n"
                   f"📌 Status: {order.get('status','Unknown')}")
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "contact":
        msg = "📞 Contact support:\n@YourSupportUsername"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "back":
        await query.edit_message_text("👋 Welcome, choose from the menu:", reply_markup=main_menu())

# ============= Running Bot =============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler))

    logger.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
