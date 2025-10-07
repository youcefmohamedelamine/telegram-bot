"""
Simple Telegram Stars Shop Bot + Web Server for Render
"""

import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, PreCheckoutQueryHandler, ContextTypes, filters

# ============================================================================
# CONFIG
# ============================================================================

BOT_TOKEN = "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg"
PORT = 8080

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# FLASK WEB SERVER (for Render)
# ============================================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!", 200

@app.route('/health')
def health():
    return {"status": "ok"}, 200

def run_flask():
    """Run Flask in background"""
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ============================================================================
# PRODUCTS
# ============================================================================

PRODUCTS = {
    "ebook": {
        "name": "Python eBook",
        "price": 10,
        "emoji": "📚",
        "desc": "Complete Python guide",
        "content": "📚 Thanks for buying!\nDownload: https://example.com/ebook"
    },
    "template": {
        "name": "Website Template",
        "price": 20,
        "emoji": "🎨",
        "desc": "Professional template",
        "content": "🎨 Your template:\nhttps://example.com/template"
    },
    "course": {
        "name": "Programming Course",
        "price": 30,
        "emoji": "🎓",
        "desc": "Full programming course",
        "content": "🎓 Course access:\nhttps://example.com/course"
    }
}

# ============================================================================
# HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show products"""
    keyboard = []
    for pid, p in PRODUCTS.items():
        keyboard.append([InlineKeyboardButton(f"{p['emoji']} {p['name']} - {p['price']} ⭐", callback_data=f"buy_{pid}")])
    
    await update.message.reply_text(
        "🛍️ *Welcome to Shop!*\n\nChoose a product:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"User {update.effective_user.id} started bot")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send invoice"""
    query = update.callback_query
    await query.answer()
    
    pid = query.data.replace("buy_", "")
    if pid not in PRODUCTS:
        return
    
    p = PRODUCTS[pid]
    
    try:
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=p['name'],
            description=p['desc'],
            payload=f"product_{pid}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(p['name'], p['price'])]
        )
        logger.info(f"Invoice sent: {pid}")
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        await query.message.reply_text("❌ Error. Please try again.")

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve payment"""
    await update.pre_checkout_query.answer(ok=True)
    logger.info("Pre-checkout approved")

async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deliver product"""
    payment = update.message.successful_payment
    pid = payment.invoice_payload.replace("product_", "")
    
    if pid in PRODUCTS:
        p = PRODUCTS[pid]
        await update.message.reply_text(
            f"✅ *Payment Successful!*\n\n{p['content']}\n\n"
            f"💫 Enjoy your purchase!\n"
            f"Type /start for more products",
            parse_mode="Markdown"
        )
        logger.info(f"Payment success: {pid}, User: {update.effective_user.id}")
    else:
        await update.message.reply_text("❌ Product not found!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Start bot + web server"""
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"✅ Flask started on port {PORT}")
    
    # Start Telegram bot
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))
    bot_app.add_handler(PreCheckoutQueryHandler(precheckout))
    bot_app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))
    bot_app.add_error_handler(error_handler)
    
    logger.info("🚀 Bot started!")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
