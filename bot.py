import logging
import json
import os
import sys
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
from aiohttp import web

# ============= الإعدادات =============
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()  # مثلاً: https://yourdomain.com
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
        logger.info(f"تم إضافة طلب: {user_id} - {category} - {amount}")
    
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
    for threshold, title in RANKS:
        if total >= threshold:
            return title
    return RANKS[-1][1]

def validate_price(category, amount):
    return category in PRICES and amount in PRICES[category]

# ============= معالج /start =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    
    total = order_manager.get_total(user_id)
    count = order_manager.get_count(user_id)
    rank = get_rank(total)
    
    import base64
    user_data = {
        "totalSpent": total,
        "orderCount": count,
        "rank": rank
    }
    encoded = base64.b64encode(json.dumps(user_data).encode()).decode()
    web_url = f"{WEB_APP_URL}?startapp={encoded}"
    
    keyboard = [[InlineKeyboardButton("🛍️ افتح المتجر", web_app=WebAppInfo(url=web_url))]]
    
    await update.message.reply_text(
        f"🌟 متجر اللاشيء 🌟\n\n"
        f"مرحباً {user.first_name}\n\n"
        f"{rank}\n"
        f"💰 إنفاقك: {total:,} ⭐\n"
        f"📦 طلباتك: {count}\n\n"
        f"اضغط الزر للدخول إلى المتجر",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"مستخدم دخل: {user.id} - {user.first_name}")

# ============= معالج البيانات من Web App =============
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        action = data.get('action')
        user = update.message.from_user
        
        logger.info(f"استقبال بيانات من Web App: {data}")
        
        if action == 'buy':
            category = data.get('category')
            amount = int(data.get('amount', 0))
            
            if not validate_price(category, amount):
                await update.message.reply_text("❌ بيانات غير صحيحة")
                logger.warning(f"محاولة شراء بمعلومات خاطئة: {user.id} - {category} - {amount}")
                return
            
            product = PRODUCTS[category]
            
            await update.message.reply_invoice(
                title=f"{product['emoji']} {product['name']}",
                description=f"✨ {product['desc']}\n\n🎁 ستحصل على:\n• ملكية حصرية للاشيء\n• ترقية اللقب التلقائية\n• دعم فني مميز",
                payload=f"order_{user.id}_{category}_{amount}_{datetime.now().timestamp()}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice("السعر", amount)],
                max_tip_amount=50000,
                suggested_tip_amounts=[1000, 5000, 10000, 25000]
            )
            
            logger.info(f"تم إرسال فاتورة: {user.id} - {category} - {amount}")
            
    except json.JSONDecodeError as e:
        logger.error(f"خطأ في تحليل JSON: {e}")
        await update.message.reply_text("❌ خطأ في البيانات المرسلة")
    except Exception as e:
        logger.error(f"خطأ في معالج Web App: {e}", exc_info=True)
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")

# ============= معالج التحقق قبل الدفع =============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"تم التحقق من الدفع: {query.from_user.id}")

# ============= معالج الدفع الناجح =============
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    payment = update.message.successful_payment
    
    try:
        parts = payment.invoice_payload.split("_")
        category = parts[2]
    except:
        category = "unknown"
    
    product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨"})
    
    order_manager.add_order(user.id, payment.total_amount, category)
    
    total = order_manager.get_total(user.id)
    old_total = total - payment.total_amount
    old_rank = get_rank(old_total)
    new_rank = get_rank(total)
    
    rank_up = ""
    if old_rank != new_rank:
        rank_up = f"\n\n🎊 ترقية اللقب!\n{old_rank} ➜ {new_rank}"
    
    await update.message.reply_text(
        f"✅ تم الدفع بنجاح!\n\n"
        f"📦 {product['emoji']} {product['name']}\n"
        f"💰 {payment.total_amount:,} ⭐\n\n"
        f"🏷️ لقبك: {new_rank}\n"
        f"💎 الإجمالي: {total:,} ⭐{rank_up}\n\n"
        f"شكراً لك ❤️"
    )
    
    logger.info(f"دفع ناجح: {user.id} - {category} - {payment.total_amount}")
    
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"📢 طلب جديد!\n\n"
                f"👤 {user.first_name} (@{user.username or 'لا يوجد'})\n"
                f"🆔 {user.id}\n"
                f"📦 {product['emoji']} {product['name']}\n"
                f"💰 {payment.total_amount:,} ⭐\n"
                f"🏷️ اللقب: {new_rank}"
            )
        except Exception as e:
            logger.error(f"خطأ في إرسال إشعار للأدمن: {e}")

# ============= معالج الأخطاء =============
async def error_handler(update, context):
    logger.error(f"خطأ: {context.error}", exc_info=context.error)
    try:
        if update and update.message:
            await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
    except:
        pass

# ============= التهيئة =============
async def post_init(application):
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت متصل: @{bot.username}")
    logger.info(f"🆔 البوت ID: {bot.id}")
    logger.info(f"📊 عدد الطلبات المحفوظة: {len(order_manager.orders)}")

# ============= التشغيل =============
def main():
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN غير صحيح أو غير موجود")
        sys.exit(1)
    
    logger.info("🚀 جاري تشغيل البوت...")
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # إضافة المعالجات
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # اختيار الطريقة حسب وجود WEBHOOK_URL
    if WEBHOOK_URL:
        logger.info(f"🌐 استخدام Webhook: {WEBHOOK_URL}")
        logger.info(f"🔌 المنفذ: {PORT}")
        
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            drop_pending_updates=True
        )
    else:
        logger.info("📡 استخدام Polling")
        logger.info("⚠️ تحذير: قد يحدث تعارض إذا كان هناك webhook مفعل")
        
        # حذف الـ webhook إن وجد
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            app.bot.delete_webhook(drop_pending_updates=True)
        )
        logger.info("✅ تم حذف webhook")
        
        logger.info("✅ البوت يعمل الآن...")
        logger.info("اضغط Ctrl+C للإيقاف")
        
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            timeout=30,
            poll_interval=0.0
        )

if __name__ == "__main__":
    main()
