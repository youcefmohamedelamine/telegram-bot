import logging
import json
import os
import sys
import requests
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
            except:
                pass
        return {}
    
    def save(self):
        try:
            with open(ORDERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.orders, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"خطأ حفظ: {e}")
    
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
    
    # معالجة الشراء من Web App
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith('buy_'):
            try:
                parts = arg.split('_')
                category = parts[1]
                amount = int(parts[2])
                
                if not validate_price(category, amount):
                    await update.message.reply_text("❌ بيانات غير صحيحة")
                    return
                
                product = PRODUCTS[category]
                
                # إرسال الفاتورة مباشرة
                await update.message.reply_invoice(
                    title=f"{product['emoji']} {product['name']}",
                    description=f"✨ {product['desc']}\n\n🎁 ستحصل على:\n• ملكية حصرية للاشيء\n• ترقية اللقب التلقائية\n• دعم فني مميز",
                    payload=f"order_{user_id}_{category}_{amount}_{datetime.now().timestamp()}",
                    provider_token="XTR",
                    currency="XTR",
                    prices=[LabeledPrice("السعر", amount)],
                    max_tip_amount=50000,
                    suggested_tip_amounts=[1000, 5000, 10000, 25000]
                )
                logger.info(f"فاتورة: {user_id} - {category} - {amount}")
                return
            except Exception as e:
                logger.error(f"خطأ deep link: {e}")
    
    # الرسالة الرئيسية
    total = order_manager.get_total(user_id)
    count = order_manager.get_count(user_id)
    rank = get_rank(total)
    
    # تشفير البيانات للـ Web App
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
        f"اضغط الزر للدخول",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============= معالج التحقق قبل الدفع =============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

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
        f"📦 {product['name']}\n"
        f"💰 {payment.total_amount:,} ⭐\n\n"
        f"🏷️ لقبك: {new_rank}\n"
        f"💎 الإجمالي: {total:,} ⭐{rank_up}\n\n"
        f"شكراً لك"
    )
    
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"📢 طلب جديد!\n\n"
                f"👤 {user.first_name}\n"
                f"🆔 {user.id}\n"
                f"📦 {product['name']}\n"
                f"💰 {payment.total_amount:,} ⭐"
            )
        except:
            pass

# ============= معالج الأخطاء =============
async def error_handler(update, context):
    logger.error(f"خطأ: {context.error}")

# ============= التهيئة =============
async def post_init(application):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
        requests.get(url, timeout=10)
        logger.info("تم حذف webhook")
    except:
        pass
    
    bot = await application.bot.get_me()
    logger.info(f"البوت متصل: @{bot.username}")

# ============= إنشاء رابط الدفع =============
from aiohttp import web

async def create_invoice(request):
    try:
        category = request.query.get("category")
        amount = int(request.query.get("amount", 0))
        
        if not validate_price(category, amount):
            return web.json_response({"error": "invalid parameters"}, status=400)

        product = PRODUCTS[category]

        link = await request.app.bot.create_invoice_link(
            title=f"{product['emoji']} {product['name']}",
            description=f"{product['desc']}",
            payload=f"web_{category}_{amount}_{datetime.now().timestamp()}",
            provider_token="XTR",
            currency="XTR",
            prices=[LabeledPrice("السعر", amount)]
        )

        return web.json_response({"invoiceUrl": link})
    except Exception as e:
        logger.error(f"خطأ إنشاء رابط الفاتورة: {e}")
        return web.json_response({"error": str(e)}, status=500)

# ============= التشغيل =============
def main():
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("BOT_TOKEN غير صحيح")
        sys.exit(1)
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # 🧩 تشغيل سيرفر ويب صغير للواجهة
    from aiohttp import web
    web_app = web.Application()
    web_app.bot = app.bot
    web_app.add_routes([web.get("/create_invoice", create_invoice)])

    import threading
    def run_web():
        web.run_app(web_app, port=8080)

    threading.Thread(target=run_web, daemon=True).start()
    
    logger.info("البوت يعمل 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
