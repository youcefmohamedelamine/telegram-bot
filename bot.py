import os
import json
import logging
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template_string
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    ContextTypes,
    filters,
)

# ============= الإعدادات =============
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # لازم يكون رقم
PRICE = 1  # السعر = نجمة واحدة
PRODUCT_TITLE = "100 لايك فري فاير"
PRODUCT_DESCRIPTION = "شراء 100 لايك لفري فاير مقابل 1 نجمة"
PAYLOAD = "freefire_likes"
PROVIDER_TOKEN = ""  # لو عندك provider حطه هنا
ORDERS_FILE = "orders.json"

# ============= اللوج =============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= تحميل الطلبات =============
orders = {}
try:
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            orders = json.load(f)
except:
    orders = {}

def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

# ============= أوامر البوت =============
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

    orders[user_id] = {
        "time": datetime.now().isoformat(),
        "amount": payment_info.total_amount,
        "status": "waiting_id"
    }
    save_orders()

    await update.message.reply_text("✅ تم الدفع! أرسل ID فري فاير الآن ✍️")

async def collect_freefire_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in orders and orders[user_id].get("status") == "waiting_id":
        freefire_id = update.message.text
        orders[user_id]["freefire_id"] = freefire_id
        orders[user_id]["status"] = "completed"
        save_orders()

        await update.message.reply_text("👌 تم استلام ID الخاص بك ✅")
        if ADMIN_ID != 0:
            await context.bot.send_message(
                ADMIN_ID,
                f"📢 طلب جديد:\n👤 @{update.message.from_user.username or 'بدون'}\n🆔 {user_id}\n🎮 فري فاير ID: {freefire_id}\n💎 {PRODUCT_TITLE}"
            )

# ============= تشغيل البوت =============
def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_button, pattern="^buy$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_freefire_id))
    logger.info("🚀 البوت يعمل...")
    app.run_polling()

# ============= واجهة ويب =============
web = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>شراء لايكات فري فاير</title>
  <style>
    body { margin:0; font-family:'Cairo',sans-serif; background:linear-gradient(135deg,#4e54c8,#8f94fb); color:white; text-align:center; }
    .card { margin:100px auto; background:rgba(255,255,255,0.1); padding:30px; border-radius:20px; max-width:400px; box-shadow:0 8px 20px rgba(0,0,0,0.3); }
    h1 { font-size:2rem; }
    p { font-size:1.1rem; margin-bottom:20px; }
    .btn { display:inline-block; padding:12px 25px; font-size:1.2rem; font-weight:bold; color:#4e54c8; background:white; border-radius:50px; text-decoration:none; }
    .btn:hover { background:#eee; transform:scale(1.05); }
  </style>
</head>
<body>
  <div class="card">
    <h1>💎 شراء 100 لايك فري فاير</h1>
    <p>ادفع عبر نجوم تليجرام واحصل على 100 لايك.</p>
    <a href="https://t.me/YourBotUsername" class="btn">🚀 ابدأ الآن</a>
  </div>
</body>
</html>
"""

@web.route("/")
def home():
    return render_template_string(HTML_PAGE)

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_bot).start()
    # لا تستعمل web.run() هنا

