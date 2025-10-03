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
# 🚨 هام: يجب استبدال هذا التوكن بتوكن البوت الحقيقي 🚨
BOT_TOKEN = "7580086418:AAFRxYUb4bKHonLQge7jIpYF8SBRRPI9tjQ" 
ADMIN_ID = 5825048491 # ID حسابك الإداري (الإدمن)
PRICE = 1000 # 1000 نجمة (قيمة بالعملة الأصغر 1000 = 10 نجوم)
PRODUCT_TITLE = "100 لايك فري فاير"
PRODUCT_DESCRIPTION = "شراء 100 لايك لفري فاير مقابل 1000 نجمة"
PAYLOAD = "freefire_likes"
PROVIDER_TOKEN = ""  # فارغ لعملة النجوم (XTR)
ORDERS_FILE = "orders.json"

# ============= إعداد اللوج =============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= تحميل/تهيئة ملف الطلبات (للحماية من انهيار الملف) =============
orders = {}
try:
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            orders = json.load(f)
        logger.info(f"✅ تم تحميل {len(orders)} طلب من الملف.")
except json.JSONDecodeError:
    logger.error("❌ خطأ في قراءة ملف orders.json. تم إعادة تهيئته.")
    orders = {} 

# دالة مساعدة لحفظ الطلبات بأمان
def save_orders():
    """حفظ بيانات الطلبات في ملف JSON مع معالجة أخطاء الكتابة."""
    try:
        with open(ORDERS_FILE, "w") as f:
            json.dump(orders, f, indent=4)
    except IOError as e:
        logger.error(f"❌ فشل في حفظ ملف الطلبات: {e}")

# ============= الأوامر ومعالجة الأخطاء =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الاستجابة لأمر /start وعرض زر الشراء."""
    try:
        keyboard = [[
            InlineKeyboardButton("💎 شراء 100 لايك (1000 نجمة)", callback_data="buy")
        ]]
        await update.message.reply_text(
            "أهلاً بك 👋\nيمكنك شراء 100 لايك لفري فاير مقابل 1000 نجمة.\n"
            "لكل مستخدم عملية واحدة فقط في اليوم.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"❌ خطأ في دالة start: {e}")

async def buy_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغط زر الشراء وإرسال الفاتورة."""
    query = update.callback_query
    user_id = str(query.from_user.id)

    try:
        # 1. التحقق من الحد الزمني (24 ساعة)
        if user_id in orders:
            last_time = datetime.fromisoformat(orders[user_id]["time"])
            if datetime.now() - last_time < timedelta(days=1):
                await query.answer("يمكنك الشراء مرة واحدة فقط كل 24 ساعة ⏳", show_alert=True)
                return
        
        # 2. إرسال الفاتورة
        prices = [LabeledPrice(PRODUCT_TITLE, PRICE)]
        await context.bot.send_invoice(
            chat_id=query.from_user.id,
            title=PRODUCT_TITLE,
            description=PRODUCT_DESCRIPTION,
            payload=PAYLOAD,
            provider_token=PROVIDER_TOKEN,
            currency="XTR", # عملة نجوم التليجرام
            prices=prices
        )
        await query.answer()

    except error.BadRequest as e:
        # معالجة أخطاء API المتعلقة بالفاتورة (مثل عدم تفعيل خاصية النجوم)
        logger.error(f"❌ خطأ في طلب الفاتورة (BadRequest): {e} للمستخدم {user_id}")
        await query.answer("❌ تعذر إرسال الفاتورة. تأكد من إعداد النجوم.", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع في دالة buy_button: {e}")
        await query.answer("❌ حدث خطأ غير متوقع. حاول مجدداً.", show_alert=True)


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق المسبق قبل إتمام عملية الدفع."""
    query = update.pre_checkout_query
    try:
        if query.invoice_payload != PAYLOAD:
            await query.answer(ok=False, error_message="خطأ في حمولة الدفع")
        else:
            await query.answer(ok=True)
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة precheckout: {e}")
        await query.answer(ok=False, error_message="خطأ داخلي في المعالجة")


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الدفع الناجح (هنا يتم إرسال رسالة الانتظار للإدمن وللمستخدم)."""
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "بدون_يوزر"
    payment_info = update.message.successful_payment
    
    try:
        # 1. حفظ حالة الطلب
        orders[user_id] = {
            "time": datetime.now().isoformat(),
            "amount": payment_info.total_amount
        }
        save_orders() 

        # 2. الرد على المستخدم (الرسالة المطلوبة)
        # رسالة: "تم قبول طلبك الرجاء انتضار"
        await update.message.reply_text("✅ تم قبول طلبك بنجاح! سيتم تنفيذه قريباً. **الرجاء الانتظار.**")
        
        # 3. إرسال إشعار نهائي للإدمن
        await context.bot.send_message(
            ADMIN_ID,
            f"✅ **طلب جديد ومكتمل (مدفوع)**\nالمستخدم: @{username}\nالتلغرام ID: {user_id}\nالمنتج: {PRODUCT_TITLE}\nالمبلغ: {payment_info.total_amount/100:.2f} نجمة (XTR)\n\n**يرجى تنفيذ الطلب يدوياً للمستخدم.**"
        )
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة successful_payment للمستخدم {user_id}: {e}")
        # إرسال إشعار للإدمن بالرغم من الخطأ
        await context.bot.send_message(
            ADMIN_ID,
            f"❌ خطأ فادح في معالجة طلب الدفع من المستخدم {user_id} (@{username}). يرجى التحقق يدوياً **وتنفيذ الطلب**."
        )


# ============= تشغيل البوت =============
def main():
    if BOT_TOKEN == "ضع_توكن_البوت_هنا":
        logger.critical("🚨 لم يتم تعيين BOT_TOKEN. يرجى وضع التوكن الخاص بك قبل التشغيل.")
        return

    try:
        logger.info("🛠️ جارٍ بناء التطبيق...")
        app = Application.builder().token(BOT_TOKEN).build()
    except Exception as e:
        logger.critical(f"❌ فشل في بناء التطبيق. تأكد من صحة BOT_TOKEN: {e}")
        return

    # إضافة الـ Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_button, pattern="^buy$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    # تم حذف معالج الرسائل النصية لأنه لم يعد مطلوباً إرسال ID فري فاير

    logger.info("🚀 البوت جاهز. بدء الاستماع للطلبات...")
    try:
        app.run_polling(poll_interval=1.0)
    except error.TelegramError as e:
        logger.critical(f"❌ خطأ في API التليجرام: {e}")
    except Exception as e:
        logger.critical(f"❌ فشل فادح في التشغيل: {e}")

if __name__ == "__main__":
    main()
