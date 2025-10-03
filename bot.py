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

# ============= الإعدادات =============
BOT_TOKEN = "ضع_توكن_البوت_هنا"
ADMIN_ID = 5825048491
PRICE = 1000
PRODUCT_TITLE = "100 لايك فري فاير"
PRODUCT_DESCRIPTION = "شراء 100 لايك لفري فاير مقابل 1000 نجمة"
PAYLOAD = "freefire_likes"
PROVIDER_TOKEN = ""  # فارغ للـ Stars
ORDERS_FILE = "orders.json"

# ============= إعداد اللوج =============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
else:
    orders = {}

# ============= الأوامر =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("💎 شراء 100 لايك (1000 نجمة)", callback_data="buy")
    ]]
    await update.message.reply_text(
        "أهلا بك 👋\nيمكنك شراء 100 لايك لفري فاير مقابل 1000 نجمة.\n"
        "لكل مستخدم عملية واحدة فقط في اليوم.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id in orders:
        last_time = datetime.fromisoformat(orders[user_id]["time"])
        if datetime.now() - last_time < timedelta(days=1):
            await query.answer("يمكنك الشراء مرة واحدة فقط كل 24 ساعة ⏳", show_alert=True)
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
    await query.answer()

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != PAYLOAD:
        await query.answer(ok=False, error_message="خطأ في الدفع")
    else:
        await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "بدون_يوزر"
    orders[user_id] = {
        "time": datetime.now().isoformat(),
        "freefire_id": None
    }
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

    await update.message.reply_text("✅ تم الدفع بنجاح! أرسل الآن ID فري فاير الخاص بك.")
    await context.bot.send_message(
        ADMIN_ID,
        f"💰 دفع جديد!\nالمستخدم: @{username}\nالتلغرام ID: {user_id}\nبانتظار ID فري فاير..."
    )

async def save_freefire_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in orders or orders[user_id]["freefire_id"] is not None:
        return

    freefire_id = update.message.text.strip()
    orders[user_id]["freefire_id"] = freefire_id
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

    await update.message.reply_text("📌 تم تسجيل ID فري فاير، سيتم تنفيذ طلبك قريباً!")
    await context.bot.send_message(
        ADMIN_ID,
        f"📩 طلب مكتمل:\nالتلغرام ID: {user_id}\nID فري فاير: {freefire_id}"
    )

# ============= تشغيل البوت =============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_button, pattern="^buy$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_freefire_id))

    app.run_polling()  # 🚀 هنا الحل بدل async معقدة

if __name__ == "__main__":
    main()
