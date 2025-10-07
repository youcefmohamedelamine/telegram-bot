"""
Telegram Stars Shop Bot - Optimized for Render.com
Simple, production-ready bot for selling products with Telegram Stars
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, PreCheckoutQueryHandler, ContextTypes, filters
)

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg")
PORT = int(os.getenv("PORT", 8080))

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================================
# PRODUCTS CATALOG
# ============================================================================

PRODUCTS = {
    "ebook_python": {
        "name": "Python eBook",
        "price": 50,
        "emoji": "📚",
        "description": "Complete Python programming guide",
        "type": "text",
        "content": "🎉 Thank you for purchasing Python eBook!\n\nDownload link: https://example.com/ebook"
    },
    "website_template": {
        "name": "Website Template",
        "price": 100,
        "emoji": "🎨",
        "description": "Professional HTML/CSS template",
        "type": "link",
        "content": "🎨 Your Website Template:\nhttps://drive.google.com/xxx"
    },
    "api_script": {
        "name": "API Script",
        "price": 75,
        "emoji": "⚡",
        "description": "Ready-to-use API wrapper",
        "type": "code",
        "content": '''import requests

class APIWrapper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.example.com"
    
    def get_data(self, endpoint):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return requests.get(f"{self.base_url}/{endpoint}", headers=headers).json()

# Usage
api = APIWrapper("your_key")
data = api.get_data("users")
print(data)'''
    },
    "workout_plan": {
        "name": "30-Day Workout Plan",
        "price": 40,
        "emoji": "💪",
        "description": "Complete home workout program",
        "type": "text",
        "content": """💪 30-Day Home Workout Plan

Week 1-2: Foundation
- Monday: Push-ups, Squats (3x15)
- Wednesday: Plank, Lunges (3x12)
- Friday: Burpees (3x10)

Week 3-4: Intensity Boost
[Full detailed plan included...]

Let's get fit! 🔥"""
    },
    "instagram_guide": {
        "name": "Instagram Growth Guide",
        "price": 60,
        "emoji": "📸",
        "description": "Proven Instagram strategies",
        "type": "text",
        "content": """📸 Instagram Growth Secrets 2025

✅ Post at 9 AM, 12 PM, 6 PM
✅ Use 20-30 relevant hashtags
✅ Create Reels daily
✅ Engage with your niche
✅ Collaborate with influencers

Full strategy guide included! 📈"""
    }
}

# ============================================================================
# TELEGRAM HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - Show product catalog"""
    keyboard = []
    row = []
    
    for product_id, product in PRODUCTS.items():
        button_text = f"{product['emoji']} {product['name']}"
        row.append(InlineKeyboardButton(button_text, callback_data=f"view_{product_id}"))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛍️ *Welcome to Digital Shop!*\n\n"
        "We accept Telegram Stars ⭐\n\n"
        "💫 Instant delivery\n"
        "🔒 Secure payments\n"
        "✅ 100% satisfaction\n\n"
        "Choose a product below:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    
    logger.info(f"User {update.effective_user.id} started bot")


async def view_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show product details"""
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.replace("view_", "")
    
    if product_id not in PRODUCTS:
        await query.message.reply_text("❌ Product not found!")
        return
    
    product = PRODUCTS[product_id]
    
    keyboard = [
        [InlineKeyboardButton(f"💳 Buy for {product['price']} ⭐", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("◀️ Back to Shop", callback_data="back_shop")]
    ]
    
    await query.edit_message_text(
        f"{product['emoji']} *{product['name']}*\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 Price: *{product['price']} Stars*\n"
        f"📦 Type: {product['type'].title()}\n\n"
        f"⚡ Instant delivery after payment!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def back_to_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main shop"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    
    for product_id, product in PRODUCTS.items():
        button_text = f"{product['emoji']} {product['name']}"
        row.append(InlineKeyboardButton(button_text, callback_data=f"view_{product_id}"))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    await query.edit_message_text(
        "🛍️ *Welcome to Digital Shop!*\n\n"
        "Choose a product below:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate purchase - Send invoice"""
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.replace("buy_", "")
    
    if product_id not in PRODUCTS:
        await query.message.reply_text("❌ Product not found!")
        return
    
    product = PRODUCTS[product_id]
    
    try:
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=f"{product['emoji']} {product['name']}",
            description=product['description'],
            payload=f"product_{product_id}",
            provider_token="",  # Empty for Telegram Stars
            currency="XTR",     # Telegram Stars currency
            prices=[LabeledPrice(product['name'], product['price'])]
        )
        
        logger.info(f"Invoice sent: {product_id} to user {query.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        await query.message.reply_text(
            "❌ Error creating invoice. Please try again."
        )


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validate payment before processing"""
    query = update.pre_checkout_query
    
    if not query.invoice_payload.startswith("product_"):
        await query.answer(ok=False, error_message="Invalid payment")
        return
    
    await query.answer(ok=True)
    logger.info(f"Pre-checkout approved for user {query.from_user.id}")


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deliver product after successful payment"""
    user = update.effective_user
    payment = update.message.successful_payment
    
    # Extract product_id from payload
    product_id = payment.invoice_payload.replace("product_", "")
    
    if product_id not in PRODUCTS:
        await update.message.reply_text("❌ Error: Product not found!")
        return
    
    product = PRODUCTS[product_id]
    
    logger.info(f"Payment successful: {product_id} by user {user.id}, amount: {payment.total_amount}")
    
    # Send confirmation
    await update.message.reply_text(
        f"✅ *Payment Successful!*\n\n"
        f"Thank you {user.first_name}! 🎉\n"
        f"Product: {product['emoji']} *{product['name']}*\n\n"
        f"📦 Delivering now...",
        parse_mode="Markdown"
    )
    
    # Deliver product based on type
    if product['type'] == 'code':
        await update.message.reply_text(
            f"```python\n{product['content']}\n```",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            product['content'],
            parse_mode="Markdown"
        )
    
    # Thank you message
    await update.message.reply_text(
        "💫 *Enjoy your purchase!*\n\n"
        "⭐ Rate us if satisfied!\n"
        "🛍️ Type /start for more products",
        parse_mode="Markdown"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An error occurred. Please try again."
            )
        except:
            pass


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found!")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(view_product, pattern="^view_"))
    application.add_handler(CallbackQueryHandler(buy_product, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(back_to_shop, pattern="^back_shop$"))
    application.add_handler(PreCheckoutQueryHandler(precheckout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🚀 Bot is starting...")
    logger.info(f"Port: {PORT}")
    
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
