import logging
import json
import os
import sys
import signal
import asyncio
from datetime import datetime

import asyncpg
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
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
PORT = int(os.getenv("PORT", 8080))
WEB_APP_URL = "https://youcefmohamedelamine.github.io/winter_land_bot/"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

# ============= مدير الطلبات =============
class OrderManager:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL غير موجود")
            sys.exit(1)
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            logger.info("✅ اتصال PostgreSQL")
            await self.create_table()
        except Exception as e:
            logger.error(f"❌ فشل DB: {e}")
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
        logger.info("✅ جدول users جاهز")

    async def get_user_data(self, user_id):
        row = await self.pool.fetchrow(
            "SELECT total_spent, order_count, rank FROM users WHERE id = $1", 
            int(user_id)
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
            DO UPDATE SET 
                total_spent = users.total_spent + $2, 
                order_count = users.order_count + 1,
                rank = $4
            """,
            int(user_id), amount, new_rank
        )
        logger.info(f"✅ حفظ: {user_id} - {category} - {amount}")
        return new_total, total_spent

order_manager = OrderManager()

# ============= دوال مساعدة =============
def get_rank(total):
    for threshold, title in RANKS:
        if total >= threshold:
            return title
    return RANKS[-1][1]

def validate_price(category, amount):
    return category in PRICES and amount in PRICES[category]

# ============= معالجات البوت =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    
    data = await order_manager.get_user_data(user_id)
    total = data['totalSpent']
    count = data['orderCount']
    rank = data['rank']
    
    keyboard = [[InlineKeyboardButton(
        "🛍️ افتح المتجر", 
        web_app=WebAppInfo(url=WEB_APP_URL)
    )]]
    
    await update.message.reply_text(
        f"🌟 متجر اللاشيء 🌟\n\n"
        f"مرحباً {user.first_name}\n\n"
        f"🏷️ لقبك: {rank}\n"
        f"💰 إنفاقك: {total:,} ⭐\n"
        f"📦 طلباتك: {count}\n\n"
        f"اضغط الزر للدخول إلى المتجر",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"👤 {user.id} - {user.first_name}")

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج بيانات WebApp - هذا هو المعالج الحاسم!"""
    try:
        user = update.effective_user
        
        # التحقق من وجود البيانات
        if not update.effective_message.web_app_data:
            logger.error("❌ لا توجد web_app_data")
            return
            
        raw_data = update.effective_message.web_app_data.data
        logger.info(f"📥 استلام من: {user.id}")
        logger.info(f"📦 البيانات: {raw_data}")
        
        # تحليل البيانات
        data = json.loads(raw_data)
        action = data.get('action')
        
        if action != 'buy':
            await update.effective_message.reply_text("❌ عملية غير معروفة")
            logger.warning(f"⚠️ عملية غير معروفة: {action}")
            return
        
        category = data.get('category')
        amount = int(data.get('amount', 0))
        
        logger.info(f"🛒 طلب شراء: {category} - {amount}")
        
        # التحقق من صحة البيانات
        if not validate_price(category, amount):
            await update.effective_message.reply_text(
                f"❌ بيانات خاطئة: {category} - {amount:,} ⭐"
            )
            logger.warning(f"⚠️ بيانات خاطئة: {category} - {amount}")
            return
        
        # جلب معلومات المنتج
        product = PRODUCTS[category]
        payload = f"order_{user.id}_{category}_{amount}_{datetime.now().timestamp()}"
        
        # إرسال الفاتورة
        await update.effective_message.reply_invoice(
            title=f"{product['emoji']} {product['name']}",
            description=f"✨ {product['desc']}",
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[{'label': "السعر", 'amount': amount}],
            max_tip_amount=50000,
            suggested_tip_amounts=[1000, 5000, 10000, 25000]
        )
        
        logger.info(f"📄 فاتورة مرسلة: {product['name']} - {amount:,} ⭐")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON خاطئ: {e}")
        await update.effective_message.reply_text("❌ بيانات غير صالحة")
    except Exception as e:
        logger.error(f"❌ خطأ WebApp: {e}", exc_info=True)
        await update.effective_message.reply_text("❌ حدث خطأ")

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"✅ تحقق: {query.from_user.id}")

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    payment = update.effective_message.successful_payment
    
    try:
        parts = payment.invoice_payload.split("_")
        category = parts[2] if len(parts) > 2 else "unknown"
    except:
        category = "unknown"
    
    product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨"})
    
    new_total, old_total = await order_manager.add_order(
        user.id, 
        payment.total_amount, 
        category
    )
    
    old_rank = get_rank(old_total)
    new_rank = get_rank(new_total)
    
    rank_up = ""
    if old_rank != new_rank:
        rank_up = f"\n\n🎊 ترقية!\n{old_rank} ➜ {new_rank}"
    
    await update.effective_message.reply_text(
        f"✅ تم الدفع!\n\n"
        f"📦 {product['emoji']} {product['name']}\n"
        f"💰 {payment.total_amount:,} ⭐\n"
        f"🏷️ {new_rank}\n"
        f"💎 الإجمالي: {new_total:,} ⭐{rank_up}\n"
        f"شكراً لك ❤️"
    )
    
    logger.info(f"💳 دفع: {user.id} - {payment.total_amount:,} ⭐")
    
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"📢 طلب جديد\n\n"
                f"👤 {user.first_name}\n"
                f"🆔 {user.id}\n"
                f"📦 {product['name']}\n"
                f"💰 {payment.total_amount:,} ⭐\n"
                f"🏷️ {new_rank}"
            )
        except Exception as e:
            logger.error(f"❌ فشل إرسال للأدمن: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ خطأ: {context.error}", exc_info=context.error)

# ============= التهيئة =============
async def post_init(application):
    await order_manager.connect()
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت: @{bot.username}")
    logger.info(f"🌐 WebApp: {WEB_APP_URL}")

async def pre_shutdown(application):
    if order_manager.pool:
        await order_manager.pool.close()
        logger.info("✅ إغلاق PostgreSQL")

# ============= التشغيل =============
def main():
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN خاطئ")
        sys.exit(1)
    
    logger.info("🚀 تشغيل البوت...")
    
    app = (Application.builder()
           .token(BOT_TOKEN)
           .post_init(post_init)
           .post_shutdown(pre_shutdown)
           .build())
    
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    
    # ✨ المعالج الأهم - يجب أن يكون قبل معالج الدفع
    app.add_handler(MessageHandler(
        filters.StatusUpdate.WEB_APP_DATA, 
        handle_web_app_data
    ))
    
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(
        filters.SUCCESSFUL_PAYMENT, 
        successful_payment
    ))
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    async def cleanup_webhook():
        try:
            await app.bot.delete_webhook(drop_pending_updates=True)
            logger.info("🧹 حذف webhook سابق")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"خطأ تنظيف: {e}")
    
    loop.run_until_complete(cleanup_webhook())

    if WEBHOOK_URL:
        logger.info("🌐 Webhook Mode")
        logger.info(f"📍 {WEBHOOK_URL}")
        
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
        
        def signal_handler(sig, frame):
            logger.info("🛑 إيقاف...")
            async def shutdown():
                await app.shutdown()
                await pre_shutdown(app)
            loop.run_until_complete(shutdown())
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
            logger.info("🛑 توقف")
            loop.run_until_complete(pre_shutdown(app))
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            loop.run_until_complete(pre_shutdown(app))
        finally:
            loop.close()

if __name__ == "__main__":
    main()
