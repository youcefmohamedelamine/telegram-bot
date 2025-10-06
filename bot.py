import logging
import os
import json
import asyncio
import sys
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, PreCheckoutQueryHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import NetworkError, BadRequest, TimedOut, TelegramError, Conflict, RetryAfter, InvalidToken
from flask import Flask, render_template_string
import threading
from functools import wraps
import time

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
BOT_TOKEN = os.getenv("BOT_TOKEN", "8050433715:AAEtNaKR1cuGfWecar6FR8FSIG2QZqmfkDU")
PORT = int(os.getenv("PORT", 8080))
WEBAPP_URL = 'https://winterlandbot-production.up.railway.app'

if not BOT_TOKEN:
    logger.critical("❌ لم يتم العثور على BOT_TOKEN!")
    sys.exit(1)

# إعداد Flask
app = Flask(__name__)

# متغيرات للتحكم في حالة البوت
bot_running = True
restart_count = 0
MAX_RESTARTS = 3

# HTML Template
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
        tg.ready();
        
        function buyProduct(productId, price) {
            try {
                tg.sendData(JSON.stringify({ 
                    product: productId, 
                    price: price 
                }));
            } catch (error) {
                console.error('Error sending data:', error);
                tg.showAlert('حدث خطأ. يرجى المحاولة مرة أخرى.');
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def webapp():
    try:
        return render_template_string(WEBAPP_HTML)
    except Exception as e:
        logger.error(f"خطأ في Flask route: {e}")
        return "خطأ في الخادم", 500

@app.route('/health')
def health():
    return {'status': 'ok', 'service': 'telegram_bot', 'bot_running': bot_running}, 200

@app.route('/favicon.ico')
def favicon():
    # إرجاع favicon فارغ لتجنب خطأ 404
    return '', 204

# قائمة المنتجات
PRODUCTS = {
    "basic": {"title": "📦 الباقة الأساسية", "price": 50},
    "premium": {"title": "💎 الباقة المميزة", "price": 150},
    "vip": {"title": "👑 الباقة الذهبية", "price": 300}
}

# Decorator متقدم لمعالجة الأخطاء مع إعادة المحاولة
def advanced_error_handler(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            for attempt in range(max_retries):
                try:
                    return await func(update, context)
                
                except RetryAfter as e:
                    wait_time = e.retry_after + 1
                    logger.warning(f"Rate limited. انتظار {wait_time} ثانية...")
                    await asyncio.sleep(wait_time)
                    if attempt < max_retries - 1:
                        continue
                    
                except NetworkError as e:
                    logger.error(f"خطأ في الشبكة (محاولة {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                        continue
                    if update and update.effective_message:
                        try:
                            await update.effective_message.reply_text("⚠️ حدث خطأ في الاتصال. يرجى المحاولة لاحقاً.")
                        except:
                            pass
                
                except TimedOut as e:
                    logger.error(f"انتهت المهلة (محاولة {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                        continue
                    if update and update.effective_message:
                        try:
                            await update.effective_message.reply_text("⏱️ انتهت مهلة الطلب. حاول مرة أخرى.")
                        except:
                            pass
                
                except BadRequest as e:
                    logger.error(f"طلب خاطئ: {e}")
                    if update and update.effective_message:
                        try:
                            await update.effective_message.reply_text("❌ حدث خطأ في معالجة الطلب.")
                        except:
                            pass
                    break  # لا نعيد المحاولة في حالة BadRequest
                
                except Conflict:
                    logger.error("تضارب في النسخ - نسخة أخرى تعمل")
                    raise  # نعيد رفع الخطأ للمعالج الرئيسي
                
                except InvalidToken:
                    logger.critical("❌ Token غير صالح!")
                    raise
                
                except TelegramError as e:
                    logger.error(f"خطأ Telegram: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                        continue
                
                except Exception as e:
                    logger.error(f"خطأ غير متوقع: {e}", exc_info=True)
                    if update and update.effective_message:
                        try:
                            await update.effective_message.reply_text("❌ حدث خطأ. تم إبلاغ المطورين.")
                        except:
                            pass
                    break
            
            return None
        return wrapper
    return decorator

# دالة البداية
@advanced_error_handler(max_retries=3)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.effective_user:
        return
    
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
@advanced_error_handler(max_retries=2)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    try:
        await query.answer()
    except:
        pass  # تجاهل أخطاء answer
    
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
@advanced_error_handler(max_retries=3)
async def webapp_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.message or not update.message.web_app_data:
        return
    
    try:
        data = json.loads(update.message.web_app_data.data)
        product_id = data.get('product')
        price = data.get('price')
        
        logger.info(f"استلام بيانات WebApp: {data}")
        
        if not product_id or product_id not in PRODUCTS:
            await update.message.reply_text("❌ منتج غير صالح")
            return
        
        product = PRODUCTS[product_id]
        
        # إرسال رسالة تأكيد
        confirmation = await update.message.reply_text(
            f"⏳ جاري تجهيز الفاتورة لـ {product['title']}...",
            parse_mode='HTML'
        )
        
        # إرسال الفاتورة
        await context.bot.send_invoice(
            chat_id=update.message.chat_id,
            title=product['title'],
            description=f"شراء {product['title']}",
            payload=f"product_{product_id}",
            provider_token="",  # فارغ للنجوم
            currency="XTR",
            prices=[LabeledPrice("المنتج", price)]
        )
        
        # حذف رسالة التأكيد
        try:
            await confirmation.delete()
        except:
            pass
        
        logger.info(f"✅ فاتورة أُرسلت - المستخدم: {update.effective_user.id} - المنتج: {product_id}")
    
    except json.JSONDecodeError as e:
        logger.error(f"فشل تحليل JSON: {e}")
        await update.message.reply_text("❌ بيانات غير صالحة")
    
    except Exception as e:
        logger.error(f"خطأ في WebApp handler: {e}", exc_info=True)
        await update.message.reply_text("❌ حدث خطأ في معالجة طلبك")

# معالجة ما قبل الدفع
@advanced_error_handler(max_retries=2)
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    
    if not query or not query.invoice_payload:
        await query.answer(ok=False, error_message="❌ فاتورة غير صالحة")
        return
    
    if not query.invoice_payload.startswith("product_"):
        await query.answer(ok=False, error_message="❌ منتج غير صالح")
        return
    
    await query.answer(ok=True)
    logger.info(f"تم الموافقة على طلب الدفع - المستخدم: {update.effective_user.id}")

# معالجة الدفع الناجح
@advanced_error_handler(max_retries=3)
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.message or not update.message.successful_payment:
        return
    
    payment = update.message.successful_payment
    
    success_text = f"""
✅ <b>تم الدفع بنجاح!</b>

شكراً لشرائك! 🎉
المبلغ المدفوع: {payment.total_amount} ⭐

تم تفعيل باقتك الآن!
"""
    
    await update.message.reply_text(success_text, parse_mode='HTML')
    logger.info(f"دفع ناجح - المستخدم: {update.effective_user.id} - المبلغ: {payment.total_amount}")

# معالج الأخطاء العام المحسّن
async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    
    if isinstance(error, Conflict):
        logger.error("⚠️ Conflict: نسخة أخرى من البوت تعمل!")
        global bot_running
        bot_running = False
        return
    
    if isinstance(error, InvalidToken):
        logger.critical("❌ Token غير صالح! إيقاف البوت...")
        bot_running = False
        return
    
    if isinstance(error, RetryAfter):
        logger.warning(f"Rate limited. انتظار {error.retry_after} ثانية...")
        return
    
    if isinstance(error, NetworkError):
        logger.error(f"خطأ في الشبكة: {error}")
        return
    
    if isinstance(error, TimedOut):
        logger.warning(f"Timeout: {error}")
        return
    
    logger.error(f"خطأ غير معالج: {error}", exc_info=error)
    
    # محاولة إرسال رسالة للمستخدم
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ عذراً، حدث خطأ مؤقت. يرجى المحاولة مرة أخرى.",
                disable_notification=True
            )
        except:
            pass

def run_flask():
    try:
        from waitress import serve
        logger.info(f"Flask يعمل على المنفذ {PORT} باستخدام Waitress")
        serve(app, host='0.0.0.0', port=PORT, threads=4)
    except ImportError:
        logger.warning("Waitress غير متوفر، استخدام Flask dev server")
        app.run(host='0.0.0.0', port=PORT, threaded=True, debug=False)
    except Exception as e:
        logger.error(f"خطأ في Flask: {e}", exc_info=True)

async def main():
    global bot_running, restart_count
    
    # تشغيل Flask في thread منفصل
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask thread بدأ")
    
    while bot_running and restart_count < MAX_RESTARTS:
        application = None
        try:
            # إنشاء التطبيق
            application = (
                Application.builder()
                .token(BOT_TOKEN)
                .concurrent_updates(True)
                .connect_timeout(30.0)
                .read_timeout(30.0)
                .write_timeout(30.0)
                .pool_timeout(30.0)
                .build()
            )
            
            # إضافة المعالجات
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CallbackQueryHandler(button_handler))
            application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data_handler))
            application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
            application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
            application.add_error_handler(global_error_handler)
            
            logger.info("🚀 البوت يعمل الآن...")
            
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                timeout=30,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30
            )
            
            # Keep running
            while bot_running:
                await asyncio.sleep(1)
        
        except Conflict:
            logger.error("⚠️ Conflict: نسخة أخرى تعمل. إيقاف...")
            bot_running = False
            break
        
        except InvalidToken:
            logger.critical("❌ Token غير صالح!")
            bot_running = False
            break
        
        except KeyboardInterrupt:
            logger.info("⏹️ إيقاف البوت بواسطة المستخدم")
            bot_running = False
            break
        
        except Exception as e:
            restart_count += 1
            logger.error(f"❌ خطأ خطير (محاولة {restart_count}/{MAX_RESTARTS}): {e}", exc_info=True)
            
            if restart_count < MAX_RESTARTS:
                logger.info(f"🔄 إعادة تشغيل البوت بعد 5 ثواني...")
                await asyncio.sleep(5)
            else:
                logger.critical("❌ تجاوز الحد الأقصى لإعادة المحاولات. إيقاف البوت.")
                bot_running = False
        
        finally:
            if application:
                try:
                    logger.info("🛑 إيقاف البوت بشكل آمن...")
                    await application.stop()
                    await application.shutdown()
                except Exception as e:
                    logger.error(f"خطأ أثناء الإيقاف: {e}")
    
    logger.info("👋 البوت توقف نهائياً")
    sys.exit(0)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ إيقاف البوت...")
    except Exception as e:
        logger.critical(f"❌ خطأ فادح: {e}", exc_info=True)
        sys.exit(1)
