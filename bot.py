import logging
import json
import os
import sys
import signal
import asyncio
from datetime import datetime

# استيراد مكتبات قاعدة البيانات 
import asyncpg
# تم إزالة: from aiohttp import web

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (Application,CommandHandler,ContextTypes,PreCheckoutQueryHandler,MessageHandler,filters)

# ============= الإعدادات =============
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
# تأكد من تعيين هذا المتغير في إعدادات Railway لخدمة winter_land_bot
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
# المنفذ الذي سيستمع إليه الخادم
PORT = int(os.getenv("PORT", 8080))
# تم إزالة: API_PORT = int(os.getenv("API_PORT", 8081))
WEB_APP_URL = "https://youcefmohamedelamine.github.io/winter_land_bot/"

# رابط الـ API الذي يستخدمه تطبيق الويب المصغر (WebApp)
API_URL_PATH = "/api" 

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= البيانات والمصفوفات (لم تتغير) =============

PRODUCTS = {
    "small": {"name": "لاشيء صغير", "emoji": "🔹", "desc": "مثالي للمبتدئين"},
    "medium": {"name": "لاشيء متوسط", "emoji": "🔷", "desc": "الأكثر شعبية"},
    "large": {"name": "لاشيء كبير", "emoji": "💠", "desc": "للمحترفين"}
}

PRICES = {
    "small": [5000, 10000, 15000],
    "medium": [20000, 30000, 40000],
    "large": [50000, 75000, 100000]
}

RANKS = [
    (500000, "إمبراطور العدم 👑"),
    (300000, "ملك اللاشيء 💎"),
    (200000, "أمير الفراغ 🏆"),
    (100000, "نبيل العدم ⭐"),
    (50000, "فارس اللاشيء 🌟"),
    (20000, "تاجر العدم ✨"),
    (10000, "مبتدئ اللاشيء 🎯"),
    (0, "زائر جديد 🌱")
]

# ============= مدير الطلبات (باستخدام PostgreSQL) =============
class OrderManager:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        # ⚠️ التعديل هنا: استخدام رابط DATABASE_URL الموحد
        DATABASE_URL = os.getenv("DATABASE_URL")
        
        if not DATABASE_URL:
            logger.error("❌ متغير DATABASE_URL غير موجود. تأكد من تعيينه في Railway!")
            sys.exit(1)
            
        try:
            # دالة create_pool تقبل الرابط الموحد مباشرة
            self.pool = await asyncpg.create_pool(
                DATABASE_URL
            )
            logger.info("✅ تم الاتصال بقاعدة بيانات PostgreSQL بنجاح!")
            await self.create_table()
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
            sys.exit(1)

    async def create_table(self):
        await self.pool.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                total_spent INT DEFAULT 0,
                order_count INT DEFAULT 0,
                rank TEXT
            )
        ''')
        logger.info("✅ تم التأكد من وجود جدول users.")

    async def get_user_data(self, user_id):
        row = await self.pool.fetchrow(
            "SELECT total_spent, order_count, rank FROM users WHERE id = $1", int(user_id)
        )
        if row:
            return {
                "totalSpent": row['total_spent'],
                "orderCount": row['order_count'],
                "rank": row['rank']
            }
        
        initial_rank = get_rank(0)
        await self.pool.execute(
            "INSERT INTO users (id, total_spent, order_count, rank) VALUES ($1, $2, $3, $4)",
            int(user_id), 0, 0, initial_rank
        )
        return {"totalSpent": 0, "orderCount": 0, "rank": initial_rank}


    async def add_order(self, user_id, amount, category):
        total_spent = await self.pool.fetchval(
            "SELECT total_spent FROM users WHERE id = $1", int(user_id)
        ) or 0
        
        new_total = total_spent + amount
        new_rank = get_rank(new_total)
        
        await self.pool.execute(
            """
            INSERT INTO users (id, total_spent, order_count, rank)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) 
            DO UPDATE SET total_spent = users.total_spent + $2, 
                          order_count = users.order_count + 1,
                          rank = $4
            """,
            int(user_id), amount, new_rank
        )
        logger.info(f"✅ طلب جديد وحفظ في DB: {user_id} - {category} - {amount}")
        return new_total, total_spent

order_manager = OrderManager()

# ============= دوال الـ API (لخدمة WebApp) (تم حذفها) =============
# دوال api_get_user و api_buy تم حذفها لأنها تستخدم aiohttp
# الذي لا يتوافق مع خادم الـ Webhook في نفس العملية/المنفذ.

# ============= دوال البوت ومعالجاته =============
def get_rank(total):
    """الحصول على اللقب بناءً على إجمالي الإنفاق"""
    for threshold, title in RANKS:
        if total >= threshold:
            return title
    return RANKS[-1][1]

def validate_price(category, amount):
    """التحقق من صحة الفئة والسعر"""
    return category in PRICES and amount in PRICES[category]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.message.from_user
    user_id = user.id
    
    data = await order_manager.get_user_data(user_id)
    total = data['totalSpent']
    count = data['orderCount']
    rank = data['rank']
    
    keyboard = [[InlineKeyboardButton("🛍️ افتح المتجر", web_app=WebAppInfo(url=WEB_APP_URL))]]
    
    await update.message.reply_text(
        f"🌟 متجر اللاشيء 🌟\n\n"
        f"مرحباً {user.first_name}\n\n"
        f"🏷️ لقبك: {rank}\n"
        f"💰 إنفاقك: {total:,} ⭐\n"
        f"📦 طلباتك: {count}\n\n"
        f"اضغط الزر للدخول إلى المتجر",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"👤 دخول: {user.id} - {user.first_name}")

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        raw_data = update.message.web_app_data.data
        
        logger.info(f"📥 بيانات من: {user.id}")
        
        data = json.loads(raw_data)
        action = data.get('action')
        
        if action != 'buy':
            await update.message.reply_text("❌ عملية غير صحيحة")
            return
        
        category = data.get('category')
        amount = int(data.get('amount', 0))
        
        if not validate_price(category, amount):
            await update.message.reply_text(f"❌ بيانات غير صالحة: {category} - {amount:,} ⭐")
            return
        
        product = PRODUCTS[category]
        payload = f"order_{user.id}_{category}_{amount}_{datetime.now().timestamp()}"
        
        await update.message.reply_invoice(
            title=f"{product['emoji']} {product['name']}",
            description=f"✨ {product['desc']}",
            payload=payload,
            provider_token="", # يجب تعيين توكن مزود الدفع هنا
            currency="XTR",
            prices=[{'label': "السعر", 'amount': amount}],
            max_tip_amount=50000,
            suggested_tip_amounts=[1000, 5000, 10000, 25000]
        )
        
        logger.info(f"📄 فاتورة: {product['name']} - {amount:,} ⭐")
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالج WebApp: {e}", exc_info=True)
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق قبل الدفع"""
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"✅ تحقق: {query.from_user.id}")

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الدفع الناجح"""
    user = update.message.from_user
    payment = update.message.successful_payment
    
    try:
        parts = payment.invoice_payload.split("_")
        category = parts[2]
    except:
        category = "unknown"
    
    product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨"})
    
    # حفظ الطلب وتحديث الإجمالي في PostgreSQL
    new_total, old_total = await order_manager.add_order(user.id, payment.total_amount, category)
    
    old_rank = get_rank(old_total)
    new_rank = get_rank(new_total)
    
    rank_up = ""
    if old_rank != new_rank:
        rank_up = f"\n\n🎊 ترقية!\n{old_rank} ➜ {new_rank}"
    
    await update.message.reply_text(
        f"✅ تم الدفع بنجاح!\n\n"
        f"📦 {product['emoji']} {product['name']}\n"
        f"💰 {payment.total_amount:,} ⭐\n"
        f"🏷️ لقبك: {new_rank}\n"
        f"💎 الإجمالي: {new_total:,} ⭐{rank_up}\n"
        f"شكراً لك ❤️"
    )
    
    logger.info(f"💳 دفع ناجح وحفظ DB: {user.id} - {payment.total_amount:,} ⭐")
    
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"📢 طلب جديد!\n\n"
                f"👤 {user.first_name}\n"
                f"🆔 {user.id}\n"
                f"📦 {product['name']}\n"
                f"💰 {payment.total_amount:,} ⭐\n"
                f"🏷️ {new_rank}"
            )
        except:
            pass

# ============= تشغيل خادم الـ API مع البوت (Web App Server) (تم حذف هذه الجزئية) =============

# تم إزالة: api_server_runner = None 
# تم إزالة: async def start_api_server(application: Application):
# تم إزالة: async def shutdown_api_server():

# ============= التهيئة والإغلاق الآمن =============

async def post_init(application):
    """بعد التهيئة"""
    await order_manager.connect()
    
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت: @{bot.username}")
    
    # تم إزالة شرط تشغيل خادم API المنفصل
    # if WEBHOOK_URL:
    # await start_api_server(application)
    
    logger.info(f"🌐 WebApp: {WEB_APP_URL}")

async def pre_shutdown(application):
    """قبل الإغلاق"""
    # تم إزالة: await shutdown_api_server()
    if order_manager.pool:
        await order_manager.pool.close()
        logger.info("✅ تم إغلاق اتصال PostgreSQL")

# ============= التشغيل =============
def main():
    """الدالة الرئيسية"""
    
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN غير صحيح")
        sys.exit(1)
    
    logger.info("🚀 تشغيل البوت...")
    
    # بناء التطبيق مع دوال التهيئة والإغلاق الجديدة
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).post_shutdown(pre_shutdown).build()
    
    # المعالجات
    app.add_error_handler(lambda u, c: logger.error(f"❌ خطأ: {c.error}"))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # ✅ حذف أي webhook سابق قبل التشغيل
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    async def cleanup_webhook():
        """تنظيف Webhook قبل البدء"""
        try:
            await app.bot.delete_webhook(drop_pending_updates=True)
            logger.info("🧹 تم حذف Webhook السابق")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"خطأ في التنظيف: {e}")
    
    loop.run_until_complete(cleanup_webhook())

    # اختيار وضع التشغيل
    if WEBHOOK_URL:
        logger.info(f"🌐 Webhook Mode")
        logger.info(f"📍 Webhook URL: {WEBHOOK_URL}")
        
        # تشغيل Webhook
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            drop_pending_updates=True,
            allowed_updates=["message", "pre_checkout_query"]
        )
    else:
        logger.info("📡 Polling Mode")
        logger.info("❌ ملاحظة: يجب تعيين WEBHOOK_URL لعمل الـ API")
        
        # ✅ معالج إيقاف نظيف (مهم لوضع Polling)
        def signal_handler(sig, frame):
            logger.info("🛑 إشارة إيقاف...")
            # يجب أن يتم الإغلاق بشكل غير متزامن
            async def shutdown_async():
                await app.shutdown()
                await pre_shutdown(app)
            loop.run_until_complete(shutdown_async())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            app.run_polling(
                drop_pending_updates=True,
                allowed_updates=["message", "pre_checkout_query"],
                close_loop=False
            )
        except KeyboardInterrupt:
            logger.info("🛑 توقف بواسطة المستخدم")
            loop.run_until_complete(pre_shutdown(app))
        except Exception as e:
            logger.error(f"❌ خطأ خطير: {e}")
            loop.run_until_complete(pre_shutdown(app))
        finally:
            loop.close()


if __name__ == "__main__":
    main()
