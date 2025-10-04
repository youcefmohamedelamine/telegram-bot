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
    filters,
    CallbackQueryHandler
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
    
    # ✅ إضافة: دالة للحصول على بيانات المستخدم
    def get_user_data(self, user_id):
        """إرجاع بيانات المستخدم بصيغة JSON"""
        user_id = str(user_id)
        total = self.get_total(user_id)
        count = self.get_count(user_id)
        rank = get_rank(total)
        
        return {
            "totalSpent": total,
            "orderCount": count,
            "rank": rank
        }

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
    """معالج أمر /start - عرض المتجر"""
    user = update.message.from_user
    user_id = user.id
    
    total = order_manager.get_total(user_id)
    count = order_manager.get_count(user_id)
    rank = get_rank(total)
    
    # ✅ الإصلاح: استخدم URL مباشر بدون ترميز
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
    logger.info(f"مستخدم دخل: {user.id} - {user.first_name}")

# ✅ إضافة: معالج لإرسال بيانات المستخدم للـ Web App
async def get_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج لإرسال بيانات المستخدم
    يُستخدم عبر رابط خاص أو command
    """
    user = update.message.from_user
    user_data = order_manager.get_user_data(user.id)
    
    await update.message.reply_text(
        f"📊 إحصائياتك:\n\n"
        f"💰 الإنفاق: {user_data['totalSpent']:,} ⭐\n"
        f"📦 الطلبات: {user_data['orderCount']}\n"
        f"🏆 اللقب: {user_data['rank']}"
    )

# ============= معالج البيانات من Web App =============
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج البيانات القادمة من Web App
    يستقبل JSON من tg.sendData() ويحوله لفاتورة دفع
    """
    try:
        user = update.message.from_user
        raw_data = update.message.web_app_data.data
        
        logger.info(f"📥 استقبال web_app_data من: {user.id} (@{user.username or 'N/A'})")
        logger.info(f"📄 البيانات: {raw_data}")
        
        data = json.loads(raw_data)
        action = data.get('action')
        
        if action != 'buy':
            logger.warning(f"⚠️ عملية غير معروفة: {action}")
            await update.message.reply_text("❌ عملية غير صحيحة")
            return
        
        category = data.get('category')
        amount = int(data.get('amount', 0))
        
        logger.info(f"🛒 طلب شراء: {category} - {amount}")
        
        if not validate_price(category, amount):
            logger.error(f"❌ بيانات غير صالحة: {category} - {amount}")
            await update.message.reply_text(
                f"❌ البيانات غير صحيحة\n\n"
                f"الفئة: {category}\n"
                f"المبلغ: {amount:,} ⭐"
            )
            return
        
        product = PRODUCTS[category]
        timestamp = datetime.now().timestamp()
        payload = f"order_{user.id}_{category}_{amount}_{timestamp}"
        
        description = (
            f"✨ {product['desc']}\n\n"
            f"🎁 ستحصل على:\n"
            f"• ملكية حصرية للاشيء\n"
            f"• ترقية اللقب التلقائية\n"
            f"• دعم فني مميز"
        )
        
        await update.message.reply_invoice(
            title=f"{product['emoji']} {product['name']}",
            description=description,
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("السعر", amount)],
            max_tip_amount=50000,
            suggested_tip_amounts=[1000, 5000, 10000, 25000]
        )
        
        logger.info(f"✅ فاتورة مُرسلة: {user.id} - {product['name']} - {amount:,} ⭐")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ خطأ JSON: {e}")
        await update.message.reply_text("❌ خطأ في قراءة البيانات")
    except ValueError as e:
        logger.error(f"❌ خطأ في القيم: {e}")
        await update.message.reply_text("❌ خطأ في معالجة المبلغ")
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}", exc_info=True)
        await update.message.reply_text("❌ حدث خطأ، يرجى المحاولة لاحقاً")

# ============= معالج التحقق قبل الدفع =============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من الطلب قبل إتمام الدفع"""
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"✅ تحقق من الدفع: {query.from_user.id}")

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
    
    # حساب اللقب الجديد
    total = order_manager.get_total(user.id)
    old_total = total - payment.total_amount
    old_rank = get_rank(old_total)
    new_rank = get_rank(total)
    
    rank_up = ""
    if old_rank != new_rank:
        rank_up = f"\n\n🎊 ترقية اللقب!\n{old_rank} ➜ {new_rank}"
    
    # رسالة التأكيد
    await update.message.reply_text(
        f"✅ تم الدفع بنجاح!\n\n"
        f"📦 {product['emoji']} {product['name']}\n"
        f"💰 {payment.total_amount:,} ⭐\n\n"
        f"🏷️ لقبك: {new_rank}\n"
        f"💎 الإجمالي: {total:,} ⭐{rank_up}\n\n"
        f"شكراً لك ❤️"
    )
    
    logger.info(f"✅ دفع ناجح: {user.id} - {category} - {payment.total_amount}")
    
    # إشعار الأدمن
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"📢 طلب جديد!\n\n"
                f"👤 {user.first_name} (@{user.username or 'لا يوجد'})\n"
                f"🆔 {user.id}\n"
                f"📦 {product['emoji']} {product['name']}\n"
                f"💰 {payment.total_amount:,} ⭐\n"
                f"🏷️ اللقب: {new_rank}\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            logger.error(f"خطأ إشعار الأدمن: {e}")

# ============= معالج الأخطاء =============
async def error_handler(update, context):
    """معالج الأخطاء العام"""
    logger.error(f"❌ خطأ: {context.error}", exc_info=context.error)
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ حدث خطأ غير متوقع\nيرجى المحاولة مرة أخرى"
            )
    except:
        pass

# ============= التهيئة =============
async def post_init(application):
    """دالة بعد تهيئة البوت"""
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت متصل: @{bot.username}")
    logger.info(f"🆔 البوت ID: {bot.id}")
    logger.info(f"📊 طلبات محفوظة: {len(order_manager.orders)}")
    logger.info(f"🌐 Web App: {WEB_APP_URL}")

# ============= التشغيل =============
def main():
    """الدالة الرئيسية"""
    
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN غير صحيح")
        sys.exit(1)
    
    logger.info("🚀 جاري تشغيل البوت...")
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # المعالجات
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", get_user_stats))  # ✅ جديد
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # التشغيل
    if WEBHOOK_URL:
        logger.info(f"🌐 Webhook: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            drop_pending_updates=True
        )
    else:
        logger.info("📡 Polling")
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            app.bot.delete_webhook(drop_pending_updates=True)
        )
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
