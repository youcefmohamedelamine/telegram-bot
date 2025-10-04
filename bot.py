import logging
import json
import os
import sys
import signal
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, WebAppInfo
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
ORDERS_FILE = "orders.json"
WEB_APP_URL = "https://youcefmohamedelamine.github.io/winter_land_bot/"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= البيانات =============
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
        self.orders = self.load()
    
    def load(self):
        if os.path.exists(ORDERS_FILE):
            try:
                with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"خطأ في تحميل الطلبات: {e}")
        return {}
    
    def save(self):
        try:
            with open(ORDERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.orders, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"خطأ في حفظ الطلبات: {e}")
    
    def add_order(self, user_id, amount, category):
        user_id = str(user_id)
        if user_id not in self.orders:
            self.orders[user_id] = []
        
        self.orders[user_id].append({
            "time": datetime.now().isoformat(),
            "amount": amount,
            "category": category
        })
        self.save()
        logger.info(f"✅ طلب جديد: {user_id} - {category} - {amount}")
    
    def get_total(self, user_id):
        user_id = str(user_id)
        if user_id not in self.orders:
            return 0
        return sum(order["amount"] for order in self.orders[user_id])
    
    def get_count(self, user_id):
        user_id = str(user_id)
        if user_id not in self.orders:
            return 0
        return len(self.orders[user_id])

order_manager = OrderManager()

# ============= الدوال المساعدة =============
def get_rank(total):
    """الحصول على اللقب بناءً على إجمالي الإنفاق"""
    for threshold, title in RANKS:
        if total >= threshold:
            return title
    return RANKS[-1][1]

def validate_price(category, amount):
    """التحقق من صحة الفئة والسعر"""
    return category in PRICES and amount in PRICES[category]

# ============= معالج /start =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.message.from_user
    user_id = user.id
    
    total = order_manager.get_total(user_id)
    count = order_manager.get_count(user_id)
    rank = get_rank(total)
    
    keyboard = [[InlineKeyboardButton("🛍️ افتح المتجر", web_app=WebAppInfo(url=WEB_APP_URL))]]
    
    await update.message.reply_text(
        f"🌟 متجر اللاشيء 🌟\n\n"
        f"مرحباً {user.first_name}\n\n"
        f"{rank}\n"
        f"💰 إنفاقك: {total:,} ⭐\n"
        f"📦 طلباتك: {count}\n\n"
        f"اضغط الزر للدخول إلى المتجر",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"👤 دخول: {user.id} - {user.first_name}")

# ============= معالج البيانات من Web App =============
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج البيانات من Web App"""
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
            description=f"✨ {product['desc']}\n\n🎁 ستحصل على:\n• ملكية حصرية للاشيء\n• ترقية اللقب التلقائية\n• دعم فني مميز",
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("السعر", amount)],
            max_tip_amount=50000,
            suggested_tip_amounts=[1000, 5000, 10000, 25000]
        )
        
        logger.info(f"📄 فاتورة: {product['name']} - {amount:,} ⭐")
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}", exc_info=True)
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")

# ============= معالج التحقق قبل الدفع =============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق قبل الدفع"""
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"✅ تحقق: {query.from_user.id}")

# ============= معالج الدفع الناجح =============
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
    
    # حفظ الطلب
    order_manager.add_order(user.id, payment.total_amount, category)
    
    # حساب اللقب
    total = order_manager.get_total(user.id)
    old_total = total - payment.total_amount
    old_rank = get_rank(old_total)
    new_rank = get_rank(total)
    
    rank_up = ""
    if old_rank != new_rank:
        rank_up = f"\n\n🎊 ترقية!\n{old_rank} ➜ {new_rank}"
    
    await update.message.reply_text(
        f"✅ تم الدفع بنجاح!\n\n"
        f"📦 {product['emoji']} {product['name']}\n"
        f"💰 {payment.total_amount:,} ⭐\n\n"
        f"🏷️ لقبك: {new_rank}\n"
        f"💎 الإجمالي: {total:,} ⭐{rank_up}\n\n"
        f"شكراً لك ❤️"
    )
    
    logger.info(f"💳 دفع ناجح: {user.id} - {payment.total_amount:,} ⭐")
    
    # إشعار الأدمن
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

# ============= معالج الأخطاء =============
async def error_handler(update, context):
    """معالج الأخطاء"""
    logger.error(f"❌ خطأ: {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ حدث خطأ")
    except:
        pass

# ============= التهيئة =============
async def post_init(application):
    """بعد التهيئة"""
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت: @{bot.username}")
    logger.info(f"🆔 ID: {bot.id}")
    logger.info(f"📊 طلبات: {len(order_manager.orders)}")
    logger.info(f"🌐 WebApp: {WEB_APP_URL}")

# ============= إيقاف آمن =============
async def shutdown(application):
    """إيقاف آمن للبوت"""
    logger.info("🛑 جاري إيقاف البوت...")
    await application.stop()
    await application.shutdown()
    logger.info("✅ تم الإيقاف بنجاح")

# ============= التشغيل =============
def main():
    """الدالة الرئيسية"""
    
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN غير صحيح")
        sys.exit(1)
    
    logger.info("🚀 تشغيل البوت...")
    
    # بناء التطبيق
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # المعالجات
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # ✅ حذف أي webhook سابق قبل التشغيل
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def cleanup():
        """تنظيف قبل البدء"""
        try:
            await app.bot.delete_webhook(drop_pending_updates=True)
            logger.info("🧹 تم حذف Webhook السابق")
            # انتظار 2 ثانية للتأكد
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"خطأ في التنظيف: {e}")
    
    loop.run_until_complete(cleanup())
    
    # اختيار وضع التشغيل
    if WEBHOOK_URL:
        logger.info(f"🌐 Webhook Mode")
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
        logger.info("✅ البوت يعمل...")
        logger.info("⏹️ اضغط Ctrl+C للإيقاف")
        
        # ✅ معالج إيقاف نظيف
        def signal_handler(sig, frame):
            logger.info("🛑 إشارة إيقاف...")
            loop.run_until_complete(shutdown(app))
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # تشغيل البوت
        try:
            app.run_polling(
                drop_pending_updates=True,
                allowed_updates=["message", "pre_checkout_query"],
                close_loop=False
            )
        except KeyboardInterrupt:
            logger.info("🛑 توقف بواسطة المستخدم")
            loop.run_until_complete(shutdown(app))
        except Exception as e:
            logger.error(f"❌ خطأ خطير: {e}")
            loop.run_until_complete(shutdown(app))
        finally:
            loop.close()

if __name__ == "__main__":
    main()
