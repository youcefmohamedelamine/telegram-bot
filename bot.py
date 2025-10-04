import logging
import json
import os
import sys
import signal
import asyncio
from datetime import datetime

# استيراد مكتبات قاعدة البيانات والـ API
import asyncpg
from aiohttp import web

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters
)

# ============= الإعدادات =============
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
# تأكد من تعيين هذا المتغير في إعدادات Railway لخدمة winter_land_bot
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
# المنفذ الذي سيستمع إليه الخادم
PORT = int(os.getenv("PORT", 8080))
WEB_APP_URL = "https://youcefmohamedelamine.github.io/winter_land_bot/"

# رابط الـ API الذي يستخدمه تطبيق الويب المصغر (WebApp)
API_URL_PATH = "/api" 

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= البيانات والمصفوفات (لم تتغير) =============
# ... (باقي تعريفات PRODUCTS, PRICES, RANKS) ...

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
        # استخدم متغرات البيئة التي وفرتها Railway للاتصال
        try:
            self.pool = await asyncpg.create_pool(
                user=os.getenv("PGUSER"),
                password=os.getenv("PGPASSWORD"),
                database=os.getenv("PGDATABASE"),
                host=os.getenv("PGHOST"),
                port=os.getenv("PGPORT", 5432)
            )
            logger.info("✅ تم الاتصال بقاعدة بيانات PostgreSQL بنجاح!")
            await self.create_table()
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
            # قد تحتاج لإيقاف التطبيق إذا فشل الاتصال بالقاعدة
            sys.exit(1)

    async def create_table(self):
        # الجدول الذي أنشأته مسبقاً
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
        # جلب بيانات المستخدم أو إنشاء سجل جديد إذا لم يكن موجوداً
        row = await self.pool.fetchrow(
            "SELECT total_spent, order_count, rank FROM users WHERE id = $1", int(user_id)
        )
        if row:
            return {
                "totalSpent": row['total_spent'],
                "orderCount": row['order_count'],
                "rank": row['rank']
            }
        
        # إذا كان المستخدم جديداً، قم بإنشاء سجل له
        initial_rank = get_rank(0)
        await self.pool.execute(
            "INSERT INTO users (id, total_spent, order_count, rank) VALUES ($1, $2, $3, $4)",
            int(user_id), 0, 0, initial_rank
        )
        return {"totalSpent": 0, "orderCount": 0, "rank": initial_rank}


    async def add_order(self, user_id, amount, category):
        # تحديث بيانات المستخدم بعد الدفع الناجح
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
        return new_total, total_spent # لإرجاع البيانات للـ WebApp

order_manager = OrderManager()

# ============= دوال الـ API (لخدمة WebApp) =============
async def api_get_user(request):
    """مسار GET /api/user/{user_id}"""
    try:
        user_id = request.match_info['user_id']
        data = await order_manager.get_user_data(user_id)
        
        # يجب أن يكون الرد متوافقاً مع توقعات ملف HTML
        return web.json_response({
            "totalSpent": data['totalSpent'],
            "orderCount": data['orderCount'],
            "rank": data['rank']
        })
    except Exception as e:
        logger.error(f"❌ خطأ في API جلب المستخدم: {e}")
        return web.json_response({"error": "فشل جلب البيانات"}, status=500)

async def api_buy(request):
    """مسار POST /api/buy (لإرسال البيانات إلى البوت)"""
    try:
        data = await request.json()
        user_id = data.get('userId')
        category = data.get('category')
        amount = data.get('amount')
        
        # الكود الخلفي لا يحتاج لحفظ الطلب هنا، فقط يؤكد أن البوت سيعالجه
        if not user_id or not category or not amount:
            return web.json_response({"error": "بيانات غير كاملة"}, status=400)

        # في حالتنا، سنستخدم هذه النقطة فقط لتأكيد أن الخادم يعمل
        return web.json_response({"status": "ok", "message": "تم إرسال الطلب، البوت سيعالجه"})
        
    except Exception as e:
        logger.error(f"❌ خطأ في API الشراء: {e}")
        return web.json_response({"error": "فشل معالجة الطلب"}, status=500)

# ============= دوال البوت ومعالجاته (تم تحديثها) =============
# ... (دوال get_rank و validate_price لم تتغير) ...

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
    """معالج أمر /start (تم تعديله لاستخدام DB)"""
    user = update.message.from_user
    user_id = user.id
    
    # جلب البيانات من PostgreSQL
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
    # ... (لم يتم تغيير هذه الدالة بشكل جوهري) ...
    # ... (تستطيع استخدامها كما هي لتوليد الفاتورة) ...
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


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الدفع الناجح (تم تعديله لاستخدام DB)"""
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
    
    # حساب اللقب
    old_rank = get_rank(old_total)
    new_rank = get_rank(new_total)
    
    rank_up = ""
    if old_rank != new_rank:
        rank_up = f"\n\n🎊 ترقية!\n{old_rank} ➜ {new_rank}"
    
    await update.message.reply_text(
        f"✅ تم الدفع بنجاح!\n\n"
        f"📦 {product['emoji']} {product['name']}\n"
        f"💰 {payment.total_amount:,} ⭐\n\n"
        f"🏷️ لقبك: {new_rank}\n"
        f"💎 الإجمالي: {new_total:,} ⭐{rank_up}\n\n"
        f"شكراً لك ❤️"
    )
    
    logger.info(f"💳 دفع ناجح وحفظ DB: {user.id} - {payment.total_amount:,} ⭐")
    
    # ... (بقية كود إشعار الأدمن) ...
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

# ============= تشغيل خادم الـ API مع البوت (Web App Server) =============

async def start_api_server(app: Application):
    """دالة لتهيئة خادم الـ API"""
    
    # تهيئة مسارات الـ API
    api_app = web.Application()
    api_app.router.add_get(f"{API_URL_PATH}/user/{{user_id}}", api_get_user)
    # مسار الشراء في الـ API لا يقوم بالشراء الفعلي، بل يمرر البيانات للبوت
    api_app.router.add_post(f"{API_URL_PATH}/buy", api_buy) 
    
    # تهيئة خادم aiohttp
    runner = web.AppRunner(api_app)
    await runner.setup()
    
    # تشغيل الخادم على المنفذ المحدد
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"✅ خادم الـ API يعمل على المنفذ: {PORT}")

# ============= التهيئة النهائية والتشغيل =============

async def post_init(application):
    """بعد التهيئة"""
    await order_manager.connect() # الاتصال بقاعدة البيانات أولاً
    
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت: @{bot.username}")
    
    # إذا كنا في وضع Webhook، قم بتشغيل خادم الـ API
    if WEBHOOK_URL:
        await start_api_server(application) # تشغيل خادم API أولاً
    
    logger.info(f"🌐 WebApp: {WEB_APP_URL}")


def main():
    """الدالة الرئيسية"""
    
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN غير صحيح")
        sys.exit(1)
    
    logger.info("🚀 تشغيل البوت...")
    
    # بناء التطبيق
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # المعالجات
    # ... (المعالجات لم تتغير) ...
    app.add_error_handler(lambda u, c: logger.error(f"❌ خطأ: {c.error}"))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(PreCheckoutQueryHandler(lambda u, c: u.pre_checkout_query.answer(ok=True)))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # اختيار وضع التشغيل
    if WEBHOOK_URL:
        logger.info(f"🌐 Webhook Mode")
        logger.info(f"📍 Webhook URL: {WEBHOOK_URL}")
        
        # يجب أن يكون البوت قادر على الرد على Webhook وطلبات الـ API على نفس المنفذ
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
        
        # تشغيل البوت في وضع Polling (للتجربة المحلية غالباً)
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "pre_checkout_query"]
        )
        

if __name__ == "__main__":
    main()
