import logging
import json
import os
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    error
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
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # ID حسابك الإداري
PRICE = 1  # 1 نجمة (الوحدة الصغيرة XTR)
PRODUCT_TITLE = "100 لايك فري فاير"
PRODUCT_DESCRIPTION = "شراء 100 لايك لفري فاير مقابل 1 نجمة"
PAYLOAD = "freefire_likes"
PROVIDER_TOKEN = ""  # فارغ لعملة النجوم
ORDERS_FILE = "orders.json"

# ============= إعداد اللوج =============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= تحميل/تهيئة ملف الطلبات =============
orders = {}
try:
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            orders = json.load(f)
except json.JSONDecodeError:
    orders = {}

def save_orders():
    try:
        with open(ORDERS_FILE, "w") as f:
            json.dump(orders, f, indent=4)
    except IOError as e:
        logger.error(f"❌ فشل في حفظ الطلبات: {e}")

# ============= الأوامر =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("💎 شراء 100 لايك (1 نجمة)", callback_data="buy")
    ]]
    await update.message.reply_text(
        "أهلاً 👋\nيمكنك شراء 100 لايك لفري فاير مقابل 1 نجمة.\n"
        "كل مستخدم مسموح له بعملية واحدة خلال 24 ساعة.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id in orders and "time" in orders[user_id]:
        last_time = datetime.fromisoformat(orders[user_id]["time"])
        if datetime.now() - last_time < timedelta(days=1):
            await query.answer("⏳ يمكنك الشراء مرة واحدة كل 24 ساعة.", show_alert=True)
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
        await query.answer(ok=False, error_message="خطأ في حمولة الدفع")
    else:
        await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "بدون_يوزر"
    payment_info = update.message.successful_payment

    # حفظ الطلب
    orders[user_id] = {
        "time": datetime.now().isoformat(),
        "amount": payment_info.total_amount,
        "status": "waiting_id"
    }
    save_orders()

    # طلب ID فري فاير من المستخدم
    await update.message.reply_text(
        "✅ تم الدفع بنجاح!\n\nمن فضلك أرسل الآن **ID حسابك في فري فاير ✍️**"
    )

async def collect_freefire_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in orders and orders[user_id].get("status") == "waiting_id":
        freefire_id = update.message.text

        # تحديث الطلب
        orders[user_id]["freefire_id"] = freefire_id
        orders[user_id]["status"] = "completed"
        save_orders()

        await update.message.reply_text("👌 تم استلام ID الخاص بك، سيتم تنفيذ طلبك قريباً ✅")

        # إشعار الإدمن
        await context.bot.send_message(
            ADMIN_ID,
            f"📢 طلب جديد مكتمل:\n"
            f"👤 المستخدم: @{update.message.from_user.username or 'بدون_يوزر'}\n"
            f"🆔 تيليجرام ID: {user_id}\n"
            f"🎮 فري فاير ID: {freefire_id}\n"
            f"💎 المنتج: {PRODUCT_TITLE}\n"
            f"💰 المبلغ: {orders[user_id]['amount']} XTR\n"
        )

# ============= تشغيل البوت =============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_button, pattern="^buy$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_freefire_id))

    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
