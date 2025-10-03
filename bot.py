from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import os

# إعداد Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الحصول على التوكن من المتغيرات البيئية
TOKEN = os.environ.get('7580086418:AAFRxYUb4bKHonLQge7jIpYF8SBRRPI9tjQ')

# دالة الرد على أمر /start
async def start(update, context):
    await update.message.reply_text(
        '🤖 مرحباً! أنا بوتك الجديد\n'
        'أرسل /help لرؤية الأوامر المتاحة'
    )

# دالة الرد على أمر /help
async def help_command(update, context):
    await update.message.reply_text(
        '📋 الأوامر المتاحة:\n'
        '/start - بدء المحادثة\n'
        '/help - عرض المساعدة\n'
        '/info - معلومات عن البوت'
    )

# دالة الرد على أمر /info
async def info(update, context):
    await update.message.reply_text(
        '✨ بوت يعمل على Railway.app\n'
        '🚀 نشط 24/7'
    )

# دالة الرد على أي رسالة نصية
async def echo(update, context):
    text = update.message.text
    await update.message.reply_text(f'قلت: {text}')

# دالة معالجة الأخطاء
async def error_handler(update, context):
    logger.error(f'حدث خطأ: {context.error}')

def main():
    """بدء البوت"""
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إضافة المعالجات (handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    logger.info('البوت بدأ العمل...')
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
