import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters
)

# ============= Settings ============
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
PROVIDER_TOKEN = ""  # فارغ لنجوم تيليجرام
ORDERS_FILE = "orders.json"
WEB_APP_URL = "YOUR_WEB_APP_URL"

# ============= Logging ============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= Product Info ============
PRODUCTS = {
    "small": {"name": "🔹 لاشيء صغير", "emoji": "🔹", "desc": "مثالي للمبتدئين"},
    "medium": {"name": "🔷 لاشيء متوسط", "emoji": "🔷", "desc": "الأكثر شعبية"},
    "large": {"name": "💠 لاشيء كبير", "emoji": "💠", "desc": "للمحترفين فقط"}
}

RANKS = [
    (500000, "👑 إمبراطور العدم"),
    (300000, "💎 ملك اللاشيء"),
    (200000, "🏆 أمير الفراغ"),
    (100000, "⭐ نبيل العدم"),
    (50000, "🌟 فارس اللاشيء"),
    (20000, "✨ تاجر العدم"),
    (10000, "🎯 مبتدئ اللاشيء"),
    (0, "🌱 زائر جديد")
]

# ============= Data Management ============
class OrderManager:
    def __init__(self, filename):
        self.filename = filename
        self.orders = self._load()
    
    def _load(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.orders, f, indent=4, ensure_ascii=False)
    
    def add_order(self, user_id, order_data):
        user_id = str(user_id)
        if user_id not in self.orders:
            self.orders[user_id] = {"history": []}
        self.orders[user_id]["history"].append(order_data)
        self.save()
    
    def get_total_spent(self, user_id):
        user_id = str(user_id)
        if user_id not in self.orders:
            return 0
        return sum(o.get("amount", 0) for o in self.orders[user_id].get("history", []))
    
    def get_order_count(self, user_id):
        user_id = str(user_id)
        if user_id not in self.orders:
            return 0
        return len(self.orders[user_id].get("history", []))

order_manager = OrderManager(ORDERS_FILE)

def get_user_title(total_spent):
    for threshold, title in RANKS:
        if total_spent >= threshold:
            return title
    return RANKS[-1][1]

# ============= Start Command ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    
    # التحقق من وجود معامل start (pay_category_amount)
    if context.args and context.args[0].startswith('pay_'):
        try:
            parts = context.args[0].split('_')
            category = parts[1]
            amount = int(parts[2])
            
            product = PRODUCTS.get(category)
            if not product:
                await update.message.reply_text("❌ منتج غير صحيح")
                return
            
            # إرسال الفاتورة مباشرة
            prices = [LabeledPrice(product["name"], amount)]
            
            await update.message.reply_invoice(
                title=f"{product['emoji']} {product['name']}",
                description=f"{product['desc']}\nالسعر: {amount:,} نجمة",
                payload=f"order_{user_id}_{category}_{amount}",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices
            )
            
            return
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            await update.message.reply_text("❌ حدث خطأ في إنشاء الفاتورة")
            return
    
    # عرض القائمة الرئيسية
    total_spent = order_manager.get_total_spent(user_id)
    user_title = get_user_title(total_spent)
    order_count = order_manager.get_order_count(user_id)
    
    keyboard = [[
        InlineKeyboardButton("🛍️ افتح المتجر", web_app={"url": WEB_APP_URL})
    ]]
    
    welcome = f"""╔══════════════════════╗
║   🌟 متجر اللاشيء 🌟   ║
╚══════════════════════╝

مرحباً *{user.first_name}*! 👋
{user_title}

💰 إجمالي إنفاقك: *{total_spent:,} ⭐*
📦 عدد طلباتك: *{order_count}*

🎭 اضغط الزر أدناه للتسوق:"""
    
    await update.message.reply_text(
        welcome,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ============= Pre-Checkout Handler ============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

# ============= Successful Payment ============
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    payment = update.message.successful_payment
    
    payload_parts = payment.invoice_payload.split("_")
    category = payload_parts[2] if len(payload_parts) > 2 else "unknown"
    
    product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨", "desc": ""})
    
    order_data = {
        "time": datetime.now().isoformat(),
        "amount": payment.total_amount,
        "category": category,
        "product": product["name"],
        "username": user.username or "Unknown"
    }
    order_manager.add_order(user_id, order_data)
    
    total_spent = order_manager.get_total_spent(user_id)
    old_total = total_spent - payment.total_amount
    old_title = get_user_title(old_total)
    new_title = get_user_title(total_spent)
    
    rank_up = ""
    if old_title != new_title:
        rank_up = f"\n\n🎊 *تهانينا! ترقية اللقب!*\n{old_title} ➜ {new_title}"
    
    success = f"""╔══════════════════════╗
║   🎉 تم الدفع بنجاح! 🎉   ║
╚══════════════════════╝

عزيزي *{user.first_name}*،

✨ تمت عملية الشراء بنجاح!

━━━━━━━━━━━━━━━━
📦 المنتج: *{product['name']}*
💰 المبلغ: *{payment.total_amount:,} ⭐*
📅 التاريخ: `{datetime.now().strftime("%Y-%m-%d %H:%M")}`
━━━━━━━━━━━━━━━━

🏷️ *لقبك الحالي:* {new_title}
💎 *إجمالي إنفاقك:* {total_spent:,} ⭐{rank_up}

━━━━━━━━━━━━━━━━
🎁 مبروك! أنت الآن مالك رسمي للاشيء
💫 شكراً لثقتك بنا! 💕"""
    
    await update.message.reply_text(success, parse_mode="Markdown")
    
    if ADMIN_ID:
        try:
            admin_msg = f"""╔══════════════════════╗
║   📢 طلب جديد!   ║
╚══════════════════════╝

👤 @{user.username or user_id}
📛 {user.first_name}
🏷️ {new_title}
📦 {product['name']}
💰 *{payment.total_amount:,} ⭐*
🕐 `{datetime.now().strftime("%Y-%m-%d %H:%M")}`"""
            
            await context.bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")

# ============= Main ============
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    logger.info("🚀 Bot is running with inline payment...")
    app.run_polling()

if __name__ == "__main__":
    main()
