import logging
from telegram import Update, LabeledPrice
from telegram.ext import Application, CommandHandler, PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ضع توكن البوت الخاص بك هنا
BOT_TOKEN = "7580086418:AAHqVeQNSAn0q8CK7EYUZUpgKuuHUApozzE"

# دالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أنا بوت للدفع بنجوم تيليجرام ⭐\n\n"
        "استخدم /buy لشراء منتج"
    )

# دالة الشراء
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    # إنشاء الفاتورة
    title = "منتج تجريبي"
    description = "هذا منتج تجريبي يمكنك شراؤه بنجوم تيليجرام"
    payload = "custom-payload"
    currency = "XTR"  # XTR هي عملة نجوم تيليجرام
    
    # السعر (عدد النجوم)
    prices = [LabeledPrice("المنتج", 100)]  # 100 نجمة
    
    # إرسال الفاتورة
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # فارغ لنجوم تيليجرام
        currency=currency,
        prices=prices
    )

# معالجة استعلامات ما قبل الدفع
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    
    # التحقق من البيانات
    if query.invoice_payload != "custom-payload":
        await query.answer(ok=False, error_message="حدث خطأ في معالجة الدفع")
    else:
        await query.answer(ok=True)

# معالجة الدفع الناجح
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    
    logger.info(f"تم الدفع بنجاح! المستخدم: {update.message.from_user.id}")
    logger.info(f"المبلغ: {payment.total_amount} {payment.currency}")
    logger.info(f"Telegram Payment Charge ID: {payment.telegram_payment_charge_id}")
    
    await update.message.reply_text(
        "✅ تم الدفع بنجاح!\n"
        f"شكراً لشرائك المنتج ⭐\n"
        f"المبلغ المدفوع: {payment.total_amount} نجمة"
    )

# دالة معالجة الأخطاء
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"حدث خطأ: {context.error}")

def main():
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_error_handler(error_handler)
    
    # تشغيل البوت
    logger.info("البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
