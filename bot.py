import logging
import json
import os
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    error # استيراد module الأخطاء
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
BOT_TOKEN = "ضع_توكن_البوت_هنا" 
ADMIN_ID = 5825048491
PRICE = 1000
PRODUCT_TITLE = "100 لايك فري فاير"
PRODUCT_DESCRIPTION = "شراء 100 لايك لفري فاير مقابل 1000 نجمة"
PAYLOAD = "freefire_likes"
PROVIDER_TOKEN = ""  # فارغ للـ Stars (XTR)
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
        logger.info(f"✅ تم تحميل {len(orders)} طلب من الملف.")
    else:
        logger.warning("⚠️ ملف الطلبات (orders.json) غير موجود، سيتم إنشاؤه لاحقاً.")
except json.JSONDecodeError:
    logger.error("❌ خطأ في قراءة ملف orders.json. تأكد من أنه بصيغة JSON صحيحة.")
    orders = {} # إعادة التهيئة كـ dict فارغ لتفادي الانهيار

# دالة مساعدة لحفظ الطلبات
def save_orders():
    """حفظ بيانات الطلبات في ملف JSON مع معالجة الأخطاء."""
    try:
        with open(ORDERS_FILE, "w") as f:
            json.dump(orders, f, indent=4)
    except IOError as e:
        logger.error(f"❌ فشل في حفظ ملف الطلبات: {e}")

# ============= الأوامر ومعالجة الأخطاء =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    query = update.callback_query
    user_id = str(query.from_user.id)

    try:
        # 1. التحقق من الحد الزمني
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
            currency="XTR",
            prices=prices
        )
        await query.answer()

    except error.BadRequest as e:
        # خطأ شائع: "العملة غير مدعومة" أو "الفاتورة غير صحيحة"
        logger.error(f"❌ خطأ في طلب الفاتورة (BadRequest): {e} للمستخدم {user_id}")
        await query.answer("❌ تعذر إرسال الفاتورة. تأكد من إعداد النجوم.", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع في دالة buy_button: {e}")
        await query.answer("❌ حدث خطأ غير متوقع. حاول مجدداً.", show_alert=True)


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    try:
        if query.invoice_payload != PAYLOAD:
            await query.answer(ok=False, error_message="خطأ في حمولة الدفع")
            logger.warning(f"⚠️ حمولة دفع غير متطابقة من المستخدم {query.from_user.id}")
        else:
            await query.answer(ok=True)
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة precheckout: {e}")
        # يتم الرد بـ False لتجنب إتمام الدفع في حالة الخطأ
        await query.answer(ok=False, error_message="خطأ داخلي في المعالجة")


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "بدون_يوزر"
    
    try:
        # 1. حفظ حالة الطلب
        orders[user_id] = {
            "time": datetime.now().isoformat(),
            "freefire_id": None
        }
        save_orders() # استخدام الدالة الآمنة للحفظ

        # 2. الرد على المستخدم
        await update.message.reply_text("✅ تم الدفع بنجاح! أرسل الآن ID فري فاير الخاص بك.")
        
        # 3. إرسال إشعار للإدمن
        await context.bot.send_message(
            ADMIN_ID,
            f"💰 دفع جديد!\nالمستخدم: @{username}\nالتلغرام ID: {user_id}\nبانتظار ID فري فاير..."
        )
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة successful_payment للمستخدم {user_id}: {e}")
        # محاولة إبلاغ الإدمن بالخطأ (لأن المستخدم قد دفع بالفعل)
        await context.bot.send_message(
            ADMIN_ID,
            f"❌ خطأ فادح في معالجة طلب الدفع من المستخدم {user_id} (@{username}). يرجى التحقق يدوياً."
        )


async def save_freefire_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    
    try:
        # 1. التحقق من حالة الطلب
        if user_id not in orders or orders[user_id].get("freefire_id") is not None:
            # إذا لم يدفع أو أرسل الـ ID مسبقاً، تجاهل الرسالة النصية
            return

        # 2. تحديث الطلب
        freefire_id = update.message.text.strip()
        
        # 💡 يمكن إضافة تحقق هنا للتأكد من أن ID فري فاير يتكون من أرقام فقط (اختياري)
        if not freefire_id.isdigit():
             await update.message.reply_text("❌ يرجى إرسال ID فري فاير بشكل صحيح (أرقام فقط).")
             return

        orders[user_id]["freefire_id"] = freefire_id
        save_orders() # استخدام الدالة الآمنة للحفظ

        # 3. الرد على المستخدم
        await update.message.reply_text("📌 تم تسجيل ID فري فاير، سيتم تنفيذ طلبك قريباً!")
        
        # 4. إشعار الإدمن
        await context.bot.send_message(
            ADMIN_ID,
            f"📩 طلب مكتمل:\nالتلغرام ID: {user_id}\nID فري فاير: **{freefire_id}**"
        )
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة save_freefire_id للمستخدم {user_id}: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء تسجيل ID فري فاير. يرجى إبلاغ الإدمن.")

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_freefire_id))

    logger.info("🚀 البوت جاهز. بدء الاستماع للطلبات...")
    try:
        # استخدام run_polling مع معالجة الأخطاء للتشغيل
        app.run_polling(poll_interval=1.0)
    except error.TelegramError as e:
        logger.critical(f"❌ خطأ في API التليجرام: {e}")
    except Exception as e:
        logger.critical(f"❌ فشل فادح في التشغيل: {e}")

if __name__ == "__main__":
    main()
