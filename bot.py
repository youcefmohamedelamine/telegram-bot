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
    
    # ترميز بيانات المستخدم لإرسالها للـ Web App
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
    """
    معالج البيانات القادمة من Web App
    يستقبل JSON من tg.sendData() ويحوله لفاتورة دفع
    """
    try:
        user = update.message.from_user
        raw_data = update.message.web_app_data.data
        
        # تسجيل البيانات الواردة
        logger.info(f"📥 استقبال web_app_data من المستخدم: {user.id} (@{user.username or 'N/A'})")
        logger.info(f"📄 البيانات الخام: {raw_data}")
        
        # تحويل JSON إلى Dictionary
        data = json.loads(raw_data)
        action = data.get('action')
        
        # التحقق من نوع العملية
        if action != 'buy':
            logger.warning(f"⚠️ عملية غير معروفة: {action}")
            await update.message.reply_text(
                "❌ عملية غير صحيحة\n"
                "يرجى المحاولة مرة أخرى"
            )
            return
        
        # استخراج معلومات المنتج
        category = data.get('category')
        amount = int(data.get('amount', 0))
        
        logger.info(f"🛒 طلب شراء: الفئة={category}, المبلغ={amount}")
        
        # التحقق من صحة البيانات
        if not validate_price(category, amount):
            logger.error(f"❌ بيانات غير صالحة: {category} - {amount}")
            await update.message.reply_text(
                "❌ البيانات المرسلة غير صحيحة\n\n"
                f"الفئة: {category}\n"
                f"المبلغ: {amount:,} ⭐\n\n"
                "يرجى اختيار منتج من القائمة"
            )
            return
        
        # الحصول على معلومات المنتج
        product = PRODUCTS[category]
        
        # إنشاء معرف فريد للطلب (payload)
        timestamp = datetime.now().timestamp()
        payload = f"order_{user.id}_{category}_{amount}_{timestamp}"
        
        logger.info(f"📋 Payload: {payload}")
        
        # إنشاء وصف تفصيلي للفاتورة
        description = (
            f"✨ {product['desc']}\n\n"
            f"🎁 ستحصل على:\n"
            f"• ملكية حصرية للاشيء\n"
            f"• ترقية اللقب التلقائية\n"
            f"• دعم فني مميز\n\n"
            f"💫 استمتع بتجربة العدم الحقيقي"
        )
        
        # إرسال الفاتورة للمستخدم
        await update.message.reply_invoice(
            title=f"{product['emoji']} {product['name']}",
            description=description,
            payload=payload,
            provider_token="",  # فارغ لاستخدام Telegram Stars
            currency="XTR",     # عملة Telegram Stars
            prices=[LabeledPrice("السعر", amount)],
            
            # إعدادات البقشيش (اختيارية)
            max_tip_amount=50000,
            suggested_tip_amounts=[1000, 5000, 10000, 25000]
        )
        
        logger.info(
            f"✅ تم إرسال الفاتورة بنجاح:\n"
            f"   المستخدم: {user.id} (@{user.username or 'N/A'})\n"
            f"   المنتج: {product['name']}\n"
            f"   المبلغ: {amount:,} ⭐"
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ خطأ في تحليل JSON: {e}")
        logger.error(f"البيانات الواردة: {update.message.web_app_data.data}")
        await update.message.reply_text(
            "❌ خطأ في قراءة البيانات\n"
            "يرجى المحاولة مرة أخرى"
        )
        
    except ValueError as e:
        logger.error(f"❌ خطأ في تحويل القيم: {e}")
        await update.message.reply_text(
            "❌ خطأ في معالجة المبلغ\n"
            "يرجى المحاولة مرة أخرى"
        )
        
    except KeyError as e:
        logger.error(f"❌ بيانات ناقصة: {e}")
        await update.message.reply_text(
            "❌ بيانات غير كاملة\n"
            "يرجى اختيار المنتج من جديد"
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع في معالج Web App: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع\n"
            "يرجى المحاولة مرة أخرى لاحقاً\n\n"
            "إذا استمرت المشكلة، تواصل مع الدعم"
        )

# ============= معالج الأزرار Inline =============
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار Inline (احتياطي)"""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data.split("_")
        if data[0] == "buy":
            category = data[1]
            amount = int(data[2])
            user = query.from_user
            
            if not validate_price(category, amount):
                await query.message.reply_text("❌ بيانات غير صحيحة")
                return
            
            product = PRODUCTS[category]
            
            await query.message.reply_invoice(
                title=f"{product['emoji']} {product['name']}",
                description=f"✨ {product['desc']}\n\n🎁 ستحصل على:\n• ملكية حصرية للاشيء\n• ترقية اللقب التلقائية\n• دعم فني مميز",
                payload=f"order_{user.id}_{category}_{amount}_{datetime.now().timestamp()}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice("السعر", amount)],
                max_tip_amount=50000,
                suggested_tip_amounts=[1000, 5000, 10000, 25000]
            )
            
            logger.info(f"✅ فاتورة من callback: {user.id} - {category} - {amount}")
    except Exception as e:
        logger.error(f"خطأ في معالج callback: {e}")

# ============= معالج التحقق قبل الدفع =============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من الطلب قبل إتمام الدفع"""
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"✅ تحقق من الدفع: {query.from_user.id} - {query.invoice_payload}")

# ============= معالج الدفع الناجح =============
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الدفع الناجح - تسجيل الطلب وإرسال التأكيد"""
    user = update.message.from_user
    payment = update.message.successful_payment
    
    try:
        # استخراج معلومات الطلب من payload
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
    
    # رسالة الترقية إن وُجدت
    rank_up = ""
    if old_rank != new_rank:
        rank_up = f"\n\n🎊 ترقية اللقب!\n{old_rank} ➜ {new_rank}"
    
    # رسالة التأكيد للمستخدم
    await update.message.reply_text(
        f"✅ تم الدفع بنجاح!\n\n"
        f"📦 {product['emoji']} {product['name']}\n"
        f"💰 {payment.total_amount:,} ⭐\n\n"
        f"🏷️ لقبك: {new_rank}\n"
        f"💎 الإجمالي: {total:,} ⭐{rank_up}\n\n"
        f"شكراً لك ❤️"
    )
    
    logger.info(f"✅ دفع ناجح: {user.id} - {category} - {payment.total_amount}")
    
    # إرسال إشعار للأدمن
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
    
    # محاولة إرسال رسالة للمستخدم
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ حدث خطأ غير متوقع\n"
                "يرجى المحاولة مرة أخرى"
            )
    except:
        pass

# ============= التهيئة =============
async def post_init(application):
    """دالة يتم تنفيذها بعد تهيئة البوت"""
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت متصل: @{bot.username}")
    logger.info(f"🆔 البوت ID: {bot.id}")
    logger.info(f"📊 طلبات محفوظة: {len(order_manager.orders)}")
    logger.info(f"🌐 Web App URL: {WEB_APP_URL}")

# ============= التشغيل =============
def main():
    """الدالة الرئيسية لتشغيل البوت"""
    
    # التحقق من التوكن
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN غير صحيح أو غير موجود")
        logger.error("يرجى تعيين المتغير البيئي BOT_TOKEN")
        sys.exit(1)
    
    logger.info("🚀 جاري تشغيل البوت...")
    
    # بناء التطبيق
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # تسجيل المعالجات
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # اختيار طريقة التشغيل (Webhook أو Polling)
    if WEBHOOK_URL:
        logger.info(f"🌐 وضع Webhook")
        logger.info(f"📍 URL: {WEBHOOK_URL}")
        logger.info(f"🔌 Port: {PORT}")
        
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "pre_checkout_query"]
        )
    else:
        logger.info("📡 وضع Polling")
        
        # حذف أي webhook سابق
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            app.bot.delete_webhook(drop_pending_updates=True)
        )
        
        logger.info("✅ البوت يعمل الآن...")
        logger.info("اضغط Ctrl+C للإيقاف")
        
        # تشغيل البوت
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "pre_checkout_query"]
        )

if __name__ == "__main__":
    main()
