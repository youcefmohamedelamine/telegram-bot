import logging
import json
import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, PreCheckoutQueryHandler

# ================== الإعدادات الضرورية ==================
# تأكد من تعيين هذه المتغيرات في Railway
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
STAR_PROVIDER_TOKEN = os.getenv("STAR_PROVIDER_TOKEN", "").strip() # رمز موفر نجوم تيليجرام
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-github-username.github.io/your-repo-name/").strip()
PORT = int(os.getenv("PORT", 8080))

# يمكنك تغيير هذه القائمة حسب منتجاتك
PRODUCTS = {
    "small": {"name": "لاشيء صغير", "amount": 5000},
    "medium": {"name": "لاشيء متوسط", "amount": 10000},
    "large": {"name": "لاشيء كبير", "amount": 20000}
}
# =======================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ================== معالجات الأوامر ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يرسل رسالة الترحيب وزر فتح الـ Web App."""
    user = update.message.from_user
    
    keyboard = [[InlineKeyboardButton(
        "🛍️ افتح المتجر", 
        web_app=WebAppInfo(url=WEB_APP_URL)
    )]]
    
    await update.message.reply_text(
        f"مرحباً {user.first_name}، اختر ما تريد من متجر اللاشيء. اضغط الزر بالأسفل:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"👤 {user.id} استخدم /start")

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يتلقى البيانات المرسلة من الـ Web App (عندما يضغط المستخدم على زر الشراء)."""
    user_id = update.effective_user.id
    raw_data = update.effective_message.web_app_data.data
    
    try:
        data = json.loads(raw_data)
        category = data.get('category')
        amount = int(data.get('amount', 0))
    except (json.JSONDecodeError, ValueError):
        await update.effective_message.reply_text("❌ بيانات المنتج غير صالحة.")
        logger.error(f"❌ [{user_id}] بيانات WebApp خاطئة: {raw_data}")
        return

    # 1. التحقق من أن المنتج والسعر موجودان وصالحين
    product_info = PRODUCTS.get(category)
    if not product_info or product_info['amount'] != amount:
        await update.effective_message.reply_text("❌ المنتج أو السعر غير مطابق للقائمة.")
        logger.warning(f"⚠️ [{user_id}] محاولة دفع بسعر غير صحيح: {category} - {amount}")
        return
    
    if not STAR_PROVIDER_TOKEN:
        await update.effective_message.reply_text("❌ لم يتم إعداد رمز الدفع على البوت.")
        return

    # 2. إعداد الفاتورة (Invoice)
    title = f"{product_info['name']} ({amount/1000:.0f}K Stars)"
    payload = f"order_{user_id}_{category}_{amount}"
    
    await update.effective_message.reply_invoice(
        title=title,
        description=f"سعر اللاشيء: {amount} نجوم.",
        payload=payload,
        provider_token=STAR_PROVIDER_TOKEN,
        currency="XTR",  # عملة نجوم تيليجرام
        prices=[{'label': "السعر", 'amount': amount}],
        is_flexible=False
    )
    logger.info(f"📄 [{user_id}] أُنشئت فاتورة لـ: {category} - {amount:,} XTR")

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يتم استدعاؤه قبل الدفع للتحقق من الفاتورة."""
    query = update.pre_checkout_query
    
    # يمكن هنا إضافة تحققات أكثر تعقيداً
    if query.currency != "XTR":
        await query.answer(ok=False, error_message="العملة غير مدعومة.")
        return
        
    await query.answer(ok=True)
    logger.info(f"✅ [{query.from_user.id}] تحقق ما قبل الدفع ناجح.")

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يتم استدعاؤه بعد الدفع الناجح."""
    user = update.effective_user
    payment = update.effective_message.successful_payment
    
    # 1. استخراج بيانات الطلب
    try:
        parts = payment.invoice_payload.split("_")
        category = parts[2]
        amount_paid = payment.total_amount
    except (IndexError, ValueError):
        category = "Unknown"
        amount_paid = payment.total_amount

    # 2. إرسال رسالة التأكيد
    await update.effective_message.reply_text(
        f"✅ تم الدفع بنجاح يا {user.first_name}!\n\n"
        f"📦 المنتج: {category.capitalize()}\n"
        f"💰 المبلغ المدفوع: {amount_paid:,} ⭐\n\n"
        f"شكراً لك!"
    )
    
    # 3. خطوة تنفيذ الخدمة (أهم خطوة)
    # ------------------------------------
    # هنا يجب أن تضع الكود الذي ينفذ عملية الشراء الحقيقية.
    # بما أن هذا الكود لا يستخدم قاعدة بيانات:
    # يمكنك إرسال إشعار إلى لوحة تحكم خارجية، أو إرسال رسالة للأدمن، إلخ.
    # logger.info(f"🔥 نفذ الآن خدمة {category} للمستخدم {user.id}")
    # ------------------------------------
    
    logger.info(f"💳 [{user.id}] دفع ناجح: {amount_paid:,} XTR لـ {category}")


# ================== التشغيل ==================

async def post_init(application):
    """يتم تشغيله بعد بناء التطبيق."""
    if not STAR_PROVIDER_TOKEN:
        logger.error("❌ STAR_PROVIDER_TOKEN غير موجود. لن يعمل الدفع.")
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت جاهز: @{bot.username}")
    logger.info(f"🌐 WebApp: {WEB_APP_URL}")


def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير موجود.")
        sys.exit(1)

    app = (Application.builder().token(BOT_TOKEN).post_init(post_init).build())

    # معالجات الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # بما أنك تستخدم Railway و GitHub، يُفترض أنك تستخدم Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN, # استخدم التوكن كمسار سري
        webhook_url=f"{os.getenv('WEBHOOK_URL')}/{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()
