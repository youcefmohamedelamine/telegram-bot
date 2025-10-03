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
ADMIN_ID = 5825048491   # ضع آيديك أنت
PRICE = 1000            # السعر بالنجوم
PRODUCT_TITLE = "100 لايك فري فاير"
PRODUCT_DESCRIPTION = "شراء 100 لايك لفري فاير مقابل 1000 نجمة"
PAYLOAD = "freefire_likes"
PROVIDER_TOKEN = ""     # للنجوم لا يحتاج
ORDERS_FILE = "orders.json"

# ============= إعداد اللوج =============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# تحميل الطلبات (حتى ما يعيد الطلب مرتين باليوم)
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
        "👋 أهلا بك\n\nيمكنك شراء 100 لايك لفري فاير مقابل 1000 نجمة.\n"
        "كل مستخدم يمكنه الشراء مرة واحدة فقط في اليوم.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    # منع تكرار الشراء خلال 24 ساعة
    if user_id in orders:
        last_time = datetime.fromisoformat(orders[user_id]["time"])
        if datetime.now() - last_time < timedelta(days=1):
            await query.answer("❌ مسموح عملية شراء واحدة كل 24 ساعة", show_alert=True)
            return

    prices = [LabeledPrice(PRODUCT_TITLE, PRICE)]
    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title=PRODUCT_TITLE,
        description=PRODUCT_DESCRIPTION,
        payload=PAYLOAD,
        provider_token=PROVIDER_TOKEN,
        currency="XTR",  # Telegram Stars
        prices=prices
    )
    await query.answer()

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != PAYLOAD:
        await query.answer(ok=False, error_message="خطأ في عملية الدفع ❌")
    else:
        await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "بدون_يوزر"

    # حفظ عملية الدفع
    orders[user_id] = {
        "time": datetime.now().isoformat(),
        "freefire_id": None
    }
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

    # رسالة للمستخدم
    await update.message.reply_text("✅ تم الدفع!\nالرجاء إرسال رقم ID فري فاير الخاص بك.")

    # إعلام المالك
    await context.bot.send_message(
        ADMIN_ID,
        f"💰 دفع جديد!\n"
        f"المستخدم: @{username}\n"
        f"تليغرام ID: {user_id}\n"
        f"بانتظار ID فري فاير..."
    )

async def save_freefire_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in orders or orders[user_id]["freefire_id"] is not None:
        return

    freefire_id = update.message.text.strip()
    orders[user_id]["freefire_id"] = freefire_id
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

    # رسالة للمستخدم
    await update.message.reply_text("📌 تم تسجيل ID فري فاير الخاص بك، سيتم تنفيذ طلبك قريباً!")

    # إعلام المالك
    await context.bot.send_message(
        ADMIN_ID,
        f"📩 طلب مكتمل:\n"
        f"تليغرام ID: {user_id}\n"
        f"ID فري فاير: {freefire_id}"
    )

# ============= تشغيل البوت =============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_button, pattern="^buy$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_freefire_id))

    app.run_polling()

if __name__ == "__main__":
    main()
