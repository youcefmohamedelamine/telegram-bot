"""
Simple Telegram Stars Shop Bot
Easy to use, production-ready
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, PreCheckoutQueryHandler, ContextTypes, filters

# ============================================================================
# CONFIG
# ============================================================================

BOT_TOKEN = "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send invoice"""
    query = update.callback_query
    await query.answer()
    
    pid = query.data.replace("buy_", "")
    if pid not in PRODUCTS:
        return
    
    p = PRODUCTS[pid]
    
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=p['name'],
        description=p['desc'],
        payload=f"product_{pid}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(p['name'], p['price'])]
    )

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve payment"""
    await update.pre_checkout_query.answer(ok=True)

async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deliver product"""
    payment = update.message.successful_payment
    pid = payment.invoice_payload.replace("product_", "")
    
    if pid in PRODUCTS:
        p = PRODUCTS[pid]
        await update.message.reply_text(f"✅ Payment successful!\n\n{p['content']}")
    
    logger.info(f"Payment: {pid}, User: {update.effective_user.id}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Start bot"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))
    
    logger.info("🚀 Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
