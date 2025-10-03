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
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
PRICE = 1
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

# ============= تحميل الطلبات =============
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

# ============= الواجهة الرئيسية =============
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💎 شراء لايكات", callback_data="buy_menu")],
        [InlineKeyboardButton("📋 معلوماتي", callback_data="my_info")],
        [InlineKeyboardButton("📞 تواصل معنا", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============= الأوامر =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت شراء لايكات فري فاير\n\n"
        "اختر من القائمة:",
        reply_markup=main_menu()
    )

# ============= التعامل مع الأزرار =============
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == "buy_menu":
        keyboard = [[InlineKeyboardButton("💎 شراء 100 لايك (1 نجمة)", callback_data="buy")],
                    [InlineKeyboardButton("⬅️ رجوع", callback_data="back")]]
        await query.edit_message_text(
            "اختر الخدمة التي تريد شراءها:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "my_info":
        order = orders.get(user_id)
        if not order:
            msg = "❌ لا يوجد لديك طلبات سابقة."
        else:
            msg = (f"📋 آخر طلب:\n"
                   f"🕒 الوقت: {order.get('time','-')}\n"
                   f"🎮 ID فري فاير: {order.get('freefire_id','❌ لم يرسل')}\n"
                   f"📌 الحالة: {order.get('status','غير معروف')}")
        keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "contact":
        msg = "📞 للتواصل مع الدعم:\n@YourSupportUsername"
        keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "back":
        await query.edit_message_text("👋 أهلاً بك، اختر من القائمة:", reply_markup=main_menu())

    elif query.data == "buy":
        if user_id in orders and "time" in orders[user_id]:
            last_time = datetime.fromisoformat(orders[user_id]["time"])
            if datetime.now() - last_time < timedelta(days=1):
                await query.answer("⏳ يمكنك الشراء مرة كل 24 ساعة.", show_alert=True)
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

# ============= الدفع =============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != PAYLOAD:
        await query.answer(ok=False, error_message="خطأ في الدفع")
    else:
        await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    payment_info = update.message.successful_payment

    orders[user_id] = {
        "time": datetime.now().isoformat(),
        "amount": payment_info.total_amount,
        "status": "waiting_id"
    }
    save_orders()

    await update.message.reply_text("✅ تم الدفع بنجاح!\n\nأرسل الآن ID حسابك في فري فاير ✍️")

async def collect_freefire_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in orders and orders[user_id].get("status") == "waiting_id":
        freefire_id = update.message.text
        orders[user_id]["freefire_id"] = freefire_id
        orders[user_id]["status"] = "completed"
        save_orders()

        await update.message.reply_text("👌 تم استلام ID الخاص بك، سيتم تنفيذ طلبك قريباً ✅")

        await context.bot.send_message(
            ADMIN_ID,
            f"📢 طلب جديد:\n"
            f"🆔 {user_id}\n"
            f"🎮 فري فاير ID: {freefire_id}\n"
            f"💎 {PRODUCT_TITLE}"
        )

# ============= تشغيل البوت =============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_freefire_id))

    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
