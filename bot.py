import logging
import os
import json
import asyncio
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, PreCheckoutQueryHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import NetworkError, BadRequest, TimedOut, TelegramError, Conflict
from flask import Flask, render_template_string
import threading
from functools import wraps

# إعداد السجلات المتقدم
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# أخذ التوكن من متغيرات البيئة
BOT_TOKEN = "7580086418:AAHqVeQNSAn0q8CK7EYUZUpgKuuHUApozzE"
PORT = int(os.getenv("PORT", 8080))
WEBAPP_URL = os.getenv('webapp_url', 'https://winterlandbot-production.up.railway.app')

if not BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على BOT_TOKEN في متغيرات البيئة!")

# إعداد Flask
app = Flask(__name__)

# HTML Template (نفس التصميم السابق)
WEBAPP_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجر النجوم</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }
        .container { max-width: 500px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; animation: fadeInDown 0.6s ease; }
        .header h1 { font-size: 32px; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 16px; opacity: 0.9; }
        .products { display: flex; flex-direction: column; gap: 20px; }
        .product-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            animation: fadeInUp 0.6s ease;
            position: relative;
            overflow: hidden;
        }
        .product-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border-color: rgba(255, 255, 255, 0.4);
        }
        .product-emoji { font-size: 48px; margin-bottom: 15px; display: block; animation: bounce 2s infinite; }
        .product-title { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
        .product-description { font-size: 14px; opacity: 0.9; margin-bottom: 15px; line-height: 1.6; }
        .features { margin: 15px 0; }
        .feature-item { display: flex; align-items: center; margin: 8px 0; font-size: 14px; }
        .feature-item::before { content: '✓'; margin-left: 8px; color: #4ade80; font-weight: bold; font-size: 16px; }
        .price-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.2);
        }
        .price { font-size: 28px; font-weight: bold; display: flex; align-items: center; gap: 5px; }
        .buy-btn {
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            color: #000;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(251, 191, 36, 0.4);
        }
        .buy-btn:hover { transform: scale(1.05); box-shadow: 0 6px 20px rgba(251, 191, 36, 0.6); }
        .buy-btn:active { transform: scale(0.95); }
        .popular-badge {
            position: absolute;
            top: 15px;
            left: 15px;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            box-shadow: 0 2px 10px rgba(239, 68, 68, 0.5);
        }
        @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        @keyframes shine { 0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); } 100% { transform: translateX(100%) translateY(100%) rotate(45deg); } }
        .product-card:nth-child(1) { animation-delay: 0.1s; }
        .product-card:nth-child(2) { animation-delay: 0.2s; }
        .product-card:nth-child(3) { animation-delay: 0.3s; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⭐ متجر النجوم ⭐</h1>
            <p>اختر الباقة المناسبة لك</p>
        </div>
        <div class="products">
            <div class="product-card">
                <span class="product-emoji">📦</span>
                <div class="product-title">الباقة الأساسية</div>
                <div class="product-description">مثالية للمبتدئين الذين يريدون البدء</div>
                <div class="features">
                    <div class="feature-item">وصول أساسي للمنصة</div>
                    <div class="feature-item">دعم فني</div>
                    <div class="feature-item">تحديثات مجانية</div>
                </div>
                <div class="price-section">
                    <div class="price">50 ⭐</div>
                    <button class="buy-btn" onclick="buyProduct('basic', 50)">شراء</button>
                </div>
            </div>
            <div class="product-card">
                <span class="popular-badge">🔥 الأكثر شهرة</span>
                <span class="product-emoji">💎</span>
                <div class="product-title">الباقة المميزة</div>
                <div class="product-description">للمستخدمين المتقدمين الذين يريدون المزيد</div>
                <div class="features">
                    <div class="feature-item">كل ميزات الأساسية</div>
                    <div class="feature-item">أولوية في الدعم</div>
                    <div class="feature-item">ميزات حصرية</div>
                    <div class="feature-item">بدون إعلانات</div>
                </div>
                <div class="price-section">
                    <div class="price">150 ⭐</div>
                    <button class="buy-btn" onclick="buyProduct('premium', 150)">شراء</button>
                </div>
            </div>
            <div class="product-card">
                <span class="product-emoji">👑</span>
                <div class="product-title">الباقة الذهبية</div>
                <div class="product-description">التجربة الكاملة مع جميع المزايا</div>
                <div class="features">
                    <div class="feature-item">كل شيء في المميزة</div>
                    <div class="feature-item">دعم VIP 24/7</div>
                    <div class="feature-item">وصول مبكر للميزات</div>
                    <div class="feature-item">محتوى حصري</div>
                    <div class="feature-item">شارة VIP الذهبية</div>
                </div>
                <div class="price-section">
                    <div class="price">300 ⭐</div>
                    <button class="buy-btn" onclick="buyProduct('vip', 300)">شراء</button>
                </div>
            </div>
        </div>
    </div>
    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();
        function buyProduct(productId, price) {
            tg.MainButton.setText('جاري المعالجة...');
            tg.MainButton.show();
            tg.sendData(JSON.stringify({ product: productId, price: price }));
        }
        tg.ready();
    </script>
</body>
</html>
"""

@app.route('/')
def webapp():
    return render_template_string(WEBAPP_HTML)

@app.route('/health')
def health():
    return {'status': 'ok', 'service': 'telegram_bot'}, 200

# قائمة المنتجات
PRODUCTS = {
    "basic": {"title": "📦 الباقة الأساسية", "price": 50},
    "premium": {"title": "💎 الباقة المميزة", "price": 150},
    "vip": {"title": "👑 الباقة الذهبية", "price": 300}
}

# Decorator لمعالجة الأخطاء
def error_handler(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except NetworkError as e:
            logger.error(f"خطأ في الشبكة: {e}")
            if update.message:
                await update.message.reply_text("⚠️ حدث خطأ في الاتصال. يرجى المحاولة لاحقاً.")
        except TimedOut as e:
            logger.error(f"انتهت المهلة: {e}")
            if update.message:
                await update.message.reply_text("⏱️ انتهت مهلة الطلب. حاول مرة أخرى.")
        except BadRequest as e:
            logger.error(f"طلب خاطئ: {e}")
            if update.message:
                await update.message.reply_text("❌ حدث خطأ في معالجة الطلب.")
        except TelegramError as e:
            logger.error(f"خطأ في تيليجرام: {e}")
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {e}", exc_info=True)
            if update.message:
                await update.message.reply_text("❌ حدث خطأ غير متوقع. تم إبلاغ المطورين.")
    return wrapper

# دالة البداية
@error_handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🛍️ فتح المتجر", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("ℹ️ معلومات", callback_data="info")],
        [InlineKeyboardButton("📞 الدعم", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🌟 <b>مرحباً {user.first_name}!</b>

أهلاً بك في متجر النجوم ⭐
اختر باقتك المفضلة وادفع بنجوم تيليجرام

💫 <i>اضغط على "فتح المتجر" لاستعراض الباقات</i>
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    logger.info(f"المستخدم {user.id} بدأ المحادثة")

# معالجة الأزرار
@error_handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "info":
        info_text = """
ℹ️ <b>معلومات المتجر</b>

🌟 نقبل الدفع بنجوم تيليجرام
⚡ معالجة فورية للطلبات
🔒 آمن ومضمون 100%
✨ دعم فني متواصل
"""
        await query.edit_message_text(info_text, parse_mode='HTML')
    
    elif query.data == "support":
        support_text = """
📞 <b>الدعم الفني</b>

تواصل معنا:
📧 Email: support@example.com
💬 Telegram: @support
"""
        await query.edit_message_text(support_text, parse_mode='HTML')

# معالجة بيانات WebApp
@error_handler
async def webapp_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        product_id = data.get('product')
        price = data.get('price')
        
        if not product_id or product_id not in PRODUCTS:
            await update.message.reply_text("❌ منتج غير صالح")
            return
        
        product = PRODUCTS[product_id]
        
        await context.bot.send_invoice(
            chat_id=update.message.chat_id,
            title=product['title'],
            description=f"شراء {product['title']}",
            payload=f"product_{product_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("المنتج", price)]
        )
        logger.info(f"فاتورة أُنشئت للمستخدم {update.effective_user.id} - المنتج: {product_id}")
    
    except json.JSONDecodeError:
        logger.error("فشل في تحليل بيانات WebApp")
        await update.message.reply_text("❌ بيانات غير صالحة")
    except Exception as e:
        logger.error(f"خطأ في معالجة WebApp: {e}")
        await update.message.reply_text("❌ حدث خطأ في معالجة طلبك")

# معالجة ما قبل الدفع
@error_handler
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    
    if not query.invoice_payload.startswith("product_"):
        await query.answer(ok=False, error_message="❌ فاتورة غير صالحة")
        return
    
    await query.answer(ok=True)
    logger.info(f"تم الموافقة على طلب الدفع للمستخدم {update.effective_user.id}")

# معالجة الدفع الناجح
@error_handler
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    
    success_text = f"""
✅ <b>تم الدفع بنجاح!</b>

شكراً لشرائك! 🎉
المبلغ المدفوع: {payment.total_amount} ⭐

تم تفعيل باقتك الآن!
"""
    
    await update.message.reply_text(success_text, parse_mode='HTML')
    logger.info(f"دفع ناجح: المستخدم {update.effective_user.id} - المبلغ: {payment.total_amount}")

# معالج الأخطاء العام
async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"حدث استثناء أثناء معالجة تحديث: {context.error}", exc_info=context.error)
    
    if isinstance(context.error, Conflict):
        logger.warning("تم اكتشاف نسختين من البوت. توقف...")
        return
    
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقاً."
            )
        except Exception:
            pass

def run_flask():
    try:
        from waitress import serve
        logger.info(f"Flask يعمل على المنفذ {PORT} باستخدام Waitress")
        serve(app, host='0.0.0.0', port=PORT, threads=4)
    except ImportError:
        logger.warning("Waitress غير متوفر، استخدام Flask dev server")
        app.run(host='0.0.0.0', port=PORT, threaded=True)

async def main():
    # تشغيل Flask في thread منفصل
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask thread بدأ")
    
    # إنشاء التطبيق
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data_handler))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_error_handler(global_error_handler)
    
    # تشغيل البوت
    logger.info("البوت يعمل الآن...")
    
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            timeout=30
        )
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("تم إيقاف البوت بواسطة المستخدم")
    except Conflict:
        logger.error("نسخة أخرى من البوت تعمل! إيقاف هذه النسخة...")
    finally:
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("إيقاف البوت...")
