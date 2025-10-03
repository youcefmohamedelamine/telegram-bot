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

# ============= SETTINGS =============
BOT_TOKEN = os.getenv("BOT_TOKEN2")   # Bot token
OWNER_ID = os.getenv("OWNER_ID2")     # Owner ID (admin)
PRICE = 1
PRODUCT_TITLE = "Nothing"
PRODUCT_DESCRIPTION = "Buy absolutely Nothing for 1 star ✨"
PAYLOAD = "nothing_purchase"
PROVIDER_TOKEN = ""  # Empty for Telegram Stars
ORDERS_FILE = "orders.json"

# ============= LOGGING =============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= LOAD ORDERS =============
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

# ============= MAIN MENU =============
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💎 Buy Nothing", callback_data="buy_menu")],
        [InlineKeyboardButton("📋 My Info", callback_data="my_info")],
        [InlineKeyboardButton("📞 Contact", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============= COMMANDS =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the *Nothing Shop*!\n\n"
        "Here you can buy **Nothing** because you already own everything 🌌\n\n"
        "Choose from the menu below:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ============= MENU HANDLER =============
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == "buy_menu":
        keyboard = [[InlineKeyboardButton("💎 Buy Nothing (1 Star)", callback_data="buy")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back")]]
        await query.edit_message_text(
            "Select your Nothing package:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "my_info":
        order = orders.get(user_id)
        if not order:
            msg = "❌ You have no previous purchases."
        else:
            msg = (f"📋 Last Purchase:\n"
                   f"🕒 Time: {order.get('time','-')}\n"
                   f"📌 Status: {order.get('status','Unknown')}")
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "contact":
        msg = "📞 Contact support: @YourSupportUsername"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "back":
        await query.edit_message_text("👋 Welcome back, choose from the menu:", reply_markup=main_menu())

    elif query.data == "buy":
        if user_id in orders and "time" in orders[user_id]:
            last_time = datetime.fromisoformat(orders[user_id]["time"])
            if datetime.now() - last_time < timedelta(days=1):
                await query.answer("⏳ You can only buy Nothing once every 24h.", show_alert=True)
                return

        prices = [LabeledPrice(PRODUCT_TITLE, PRICE)]
        await context.bot.send_invoice(
            chat_id=query.from_user.id,
            title=PRODUCT_TITLE,
            description=PRODUCT_DESCRIPTION,
            payload=PAYLOAD,
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )

# ============= PAYMENT =============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != PAYLOAD:
        await query.answer(ok=False, error_message="Payment error")
    else:
        await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user = update.message.from_user
    payment_info = update.message.successful_payment

    orders[user_id] = {
        "time": datetime.now().isoformat(),
        "amount": payment_info.total_amount,
        "status": "completed"
    }
    save_orders()

    # 🎭 Final message: you bought nothing
    await update.message.reply_text(
        "✅ Thank you!\n\nYou successfully purchased **Nothing** 🎉\n\n"
        "But remember... you already own everything 🌌",
        parse_mode="Markdown"
    )

    # Notify owner
    if OWNER_ID:
        await context.bot.send_message(
            OWNER_ID,
            f"📢 User {user.first_name} (@{user.username}) bought NOTHING ✨"
        )

# ============= RUN BOT =============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    logger.info("🚀 Nothing Shop Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
