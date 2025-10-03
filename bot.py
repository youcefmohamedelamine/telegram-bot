import logging
import os
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ============= إعدادات البوت =============
BOT_TOKEN2 = "PUT-YOUR-BOT-TOKEN-HERE"
OWNER_ID2 = 123456789  # ضع هنا ID المالك

PRODUCT_TITLE = "Buy Nothing"
PRODUCT_DESCRIPTION = "Because those who own everything can afford to buy nothing."
PAYLOAD = "buy_nothing"
PROVIDER_TOKEN = ""  # فارغ لأنه Telegram Stars
CURRENCY = "XTR"

# الأسعار المتدرجة
PRICES = [
    LabeledPrice("Buy Nothing (10,000 Stars)", 10_000),
    LabeledPrice("Buy Nothing (20,000 Stars)", 20_000),
    LabeledPrice("Buy Nothing (30,000 Stars)", 30_000),
    LabeledPrice("Buy Nothing (40,000 Stars)", 40_000),
    LabeledPrice("Buy Nothing (50,000 Stars)", 50_000),
    LabeledPrice("Buy Nothing (60,000 Stars)", 60_000),
    LabeledPrice("Buy Nothing (70,000 Stars)", 70_000),
    LabeledPrice("Buy Nothing (80,000 Stars)", 80_000),
    LabeledPrice("Buy Nothing (90,000 Stars)", 90_000),
    LabeledPrice("Buy Nothing (100,000 Stars)", 100_000),
]

# ============= إعداد اللوج =============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= الواجهة =============
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💸 Buy Nothing", callback_data="buy_menu")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("📞 Contact", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============= الأوامر =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Nothing Shop!\n\n"
        "Here, you can buy *nothing*... literally.\n"
        "Only those who have everything can afford nothing.\n\n"
        "Choose from the menu:",
        reply_markup=main_menu()
    )

# ============= الأزرار =============
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy_menu":
        keyboard = [
            [InlineKeyboardButton("💸 Buy Nothing", callback_data="buy")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
        ]
        await query.edit_message_text(
            "Choose how much nothing you want to buy:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "info":
        await query.edit_message_text(
            "ℹ️ This is a philosophical shop.\n\n"
            "You buy nothing, but in return you prove you own everything.",
            reply_markup=main_menu()
        )

    elif query.data == "contact":
        await query.edit_message_text(
            "📞 Contact the creator:\n@YourSupportUsername",
            reply_markup=main_menu()
        )

    elif query.data == "back":
        await query.edit_message_text("👋 Welcome back!", reply_markup=main_menu())

    elif query.data == "buy":
        await context.bot.send_invoice(
            chat_id=query.from_user.id,
            title=PRODUCT_TITLE,
            description=PRODUCT_DESCRIPTION,
            payload=PAYLOAD,
            provider_token=PROVIDER_TOKEN,
            currency=CURRENCY,
            prices=PRICES
        )

# ============= الدفع =============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != PAYLOAD:
        await query.answer(ok=False, error_message="Payment error!")
    else:
        await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    amount = update.message.successful_payment.total_amount

    # رسالة للمستخدم
    await update.message.reply_text(
        f"✅ Congratulations {user.first_name}!\n\n"
        f"You have just bought *Nothing* for {amount} Stars.\n\n"
        "Nothing is now officially yours. 🌀\n"
        "Remember: only those who own everything can afford nothing."
    )

    # إشعار للمالك
    await context.bot.send_message(
        OWNER_ID2,
        f"📢 New purchase!\n"
        f"User: {user.id} ({user.first_name})\n"
        f"Bought Nothing for {amount} Stars."
    )

# ============= تشغيل البوت =============
def main():
    app = Application.builder().token(BOT_TOKEN2).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    logger.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
