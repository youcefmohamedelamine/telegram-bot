import logging
import json
import os
import signal
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
PROVIDER_TOKEN = ""
ORDERS_FILE = "orders.json"
WEB_APP_URL = "https://youcefmohamedelamine.github.io/winter_land_bot/"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

class OrderManager:
    def __init__(self, filename):
        self.filename = filename
        self.orders = self._load()
    
    def _load(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading orders: {e}")
        return {}
    
    def save(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.orders, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving orders: {e}")
    
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
    
    def get_total_users(self):
        return len(self.orders)
    
    def get_total_revenue(self):
        total = 0
        for user_data in self.orders.values():
            total += sum(o.get("amount", 0) for o in user_data.get("history", []))
        return total

order_manager = OrderManager(ORDERS_FILE)

def get_user_title(total_spent):
    for threshold, title in RANKS:
        if total_spent >= threshold:
            return title
    return RANKS[-1][1]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    
    if context.args and context.args[0].startswith('buy_'):
        try:
            parts = context.args[0].split('_')
            if len(parts) >= 3:
                category = parts[1]
                amount = int(parts[2])
                
                product = PRODUCTS.get(category)
                if not product:
                    await update.message.reply_text("❌ منتج غير صحيح")
                    return
                
                prices = [LabeledPrice(product["name"], amount)]
                
                await update.message.reply_invoice(
                    title=f"{product['emoji']} {product['name']}",
                    description=f"{product['desc']}\n💰 السعر: {amount:,} نجمة ⭐",
                    payload=f"order_{user_id}_{category}_{amount}_{datetime.now().timestamp()}",
                    provider_token=PROVIDER_TOKEN,
                    currency="XTR",
                    prices=prices
                )
                return
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            await update.message.reply_text("❌ حدث خطأ في إنشاء الفاتورة، حاول مرة أخرى")
            return
    
    total_spent = order_manager.get_total_spent(user_id)
    user_title = get_user_title(total_spent)
    order_count = order_manager.get_order_count(user_id)
    
    user_data = {
        "totalSpent": total_spent,
        "orderCount": order_count,
        "rank": user_title
    }
    
    import base64
    encoded_data = base64.b64encode(json.dumps(user_data).encode()).decode()
    web_url = f"{WEB_APP_URL}?startapp={encoded_data}"
    
    keyboard = [[InlineKeyboardButton("🛍️ افتح المتجر", web_app={"url": web_url})]]
    
    welcome = f"""╔══════════════════════╗
║   🌟 متجر اللاشيء 🌟   ║
╚══════════════════════╝

مرحباً يا {user.first_name} 👋

{user_title}

━━━━━━━━━━━━━━━━
💰 إجمالي إنفاقك: {total_spent:,} ⭐
📦 عدد طلباتك: {order_count}
━━━━━━━━━━━━━━━━

🎭 اضغط الزر أدناه لفتح المتجر
أو استخدم الأمر:
/buy لعرض المنتجات"""
    
    await update.message.reply_text(
        welcome, 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    
    keyboard.append([
        InlineKeyboardButton("🔹 5K ⭐", callback_data="buy_small_5000"),
        InlineKeyboardButton("🔹 10K ⭐", callback_data="buy_small_10000"),
        InlineKeyboardButton("🔹 15K ⭐", callback_data="buy_small_15000")
    ])
    
    keyboard.append([
        InlineKeyboardButton("🔷 20K ⭐", callback_data="buy_medium_20000"),
        InlineKeyboardButton("🔷 30K ⭐", callback_data="buy_medium_30000"),
        InlineKeyboardButton("🔷 40K ⭐", callback_data="buy_medium_40000")
    ])
    
    keyboard.append([
        InlineKeyboardButton("💠 50K ⭐", callback_data="buy_large_50000"),
        InlineKeyboardButton("💠 75K ⭐", callback_data="buy_large_75000"),
        InlineKeyboardButton("💠 100K ⭐", callback_data="buy_large_100000")
    ])
    
    text = """🛍️ اختر المنتج والسعر:

🔹 لاشيء صغير - مثالي للمبتدئين
🔷 لاشيء متوسط - الأكثر شعبية  
💠 لاشيء كبير - للمحترفين فقط"""
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = str(user.id)
    
    try:
        parts = query.data.split('_')
        category = parts[1]
        amount = int(parts[2])
        
        product = PRODUCTS.get(category)
        if not product:
            await query.message.reply_text("❌ منتج غير صحيح")
            return
        
        prices = [LabeledPrice(product["name"], amount)]
        
        await query.message.reply_invoice(
            title=f"{product['emoji']} {product['name']}",
            description=f"{product['desc']}\n💰 السعر: {amount:,} نجمة ⭐",
            payload=f"order_{user_id}_{category}_{amount}_{datetime.now().timestamp()}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )
    except Exception as e:
        logger.error(f"Error in buy callback: {e}")
        await query.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    payment = update.message.successful_payment
    
    try:
        payload_parts = payment.invoice_payload.split("_")
        category = payload_parts[2] if len(payload_parts) > 2 else "unknown"
        
        product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨", "desc": ""})
        
        order_data = {
            "time": datetime.now().isoformat(),
            "amount": payment.total_amount,
            "category": category,
            "product": product["name"],
            "username": user.username or "Unknown",
            "user_id": user.id
        }
        order_manager.add_order(user_id, order_data)
        
        total_spent = order_manager.get_total_spent(user_id)
        old_total = total_spent - payment.total_amount
        old_title = get_user_title(old_total)
        new_title = get_user_title(total_spent)
        
        rank_up = ""
        if old_title != new_title:
            rank_up = f"\n\n🎊 تهانينا! ترقية اللقب!\n{old_title} ➜ {new_title}"
        
        success = f"""╔══════════════════════╗
║   🎉 تم الدفع بنجاح! 🎉   ║
╚══════════════════════╝

عزيزي {user.first_name}،

✨ تمت عملية الشراء بنجاح!

━━━━━━━━━━━━━━━━
📦 المنتج: {product['name']}
💰 المبلغ: {payment.total_amount:,} ⭐
📅 التاريخ: {datetime.now().strftime("%Y-%m-%d %H:%M")}
━━━━━━━━━━━━━━━━

🏷️ لقبك الحالي: {new_title}
💎 إجمالي إنفاقك: {total_spent:,} ⭐{rank_up}

━━━━━━━━━━━━━━━━
🎁 مبروك! أنت الآن مالك رسمي للاشيء
💫 شكراً لثقتك بنا!

استخدم /start للعودة للمتجر"""
        
        await update.message.reply_text(success)
        
        if ADMIN_ID:
            try:
                admin_msg = f"""╔══════════════════════╗
║   📢 طلب جديد!   ║
╚══════════════════════╝

👤 المستخدم: @{user.username or 'بدون يوزر'}
🆔 ID: {user.id}
📛 الاسم: {user.first_name}
🏷️ اللقب: {new_title}

📦 المنتج: {product['name']}
💰 المبلغ: {payment.total_amount:,} ⭐
💎 الإجمالي: {total_spent:,} ⭐

🕐 الوقت: {datetime.now().strftime("%Y-%m-%d %H:%M")}"""
                
                await context.bot.send_message(ADMIN_ID, admin_msg)
            except Exception as e:
                logger.error(f"Error sending admin notification: {e}")
    
    except Exception as e:
        logger.error(f"Error in successful_payment: {e}")
        await update.message.reply_text("✅ تم الدفع بنجاح!\nحدث خطأ في حفظ الطلب، تواصل مع الدعم")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    
    # إحصائيات عامة للأدمن
    if str(user.id) == ADMIN_ID:
        total_users = order_manager.get_total_users()
        total_revenue = order_manager.get_total_revenue()
        
        admin_stats = f"""╔══════════════════════╗
║   📊 إحصائيات عامة   ║
╚══════════════════════╝

👥 إجمالي المستخدمين: {total_users}
💰 إجمالي الإيرادات: {total_revenue:,} ⭐

━━━━━━━━━━━━━━━━"""
        await update.message.reply_text(admin_stats)
    
    total_spent = order_manager.get_total_spent(user_id)
    order_count = order_manager.get_order_count(user_id)
    user_title = get_user_title(total_spent)
    
    next_rank_info = ""
    for threshold, title in RANKS:
        if total_spent < threshold:
            remaining = threshold - total_spent
            progress = (total_spent / threshold) * 100
            next_rank_info = f"\n\n📊 التقدم للرتبة القادمة:\n{title}\n🎯 المتبقي: {remaining:,} ⭐\n📈 التقدم: {progress:.1f}%"
            break
    
    if not next_rank_info:
        next_rank_info = "\n\n🏆 تهانينا! وصلت لأعلى رتبة!"
    
    stats = f"""╔══════════════════════╗
║   📊 إحصائياتك   ║
╚══════════════════════╝

👤 الاسم: {user.first_name}
🏷️ اللقب: {user_title}

━━━━━━━━━━━━━━━━
💰 إجمالي الإنفاق: {total_spent:,} ⭐
📦 عدد الطلبات: {order_count}
💵 متوسط الطلب: {(total_spent // order_count) if order_count > 0 else 0:,} ⭐{next_rank_info}

━━━━━━━━━━━━━━━━
استخدم /buy للتسوق الآن!"""
    
    await update.message.reply_text(stats)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """╔══════════════════════╗
║   📖 المساعدة   ║
╚══════════════════════╝

الأوامر المتاحة:

/start - الصفحة الرئيسية
/buy - عرض المنتجات
/stats - إحصائياتك
/ranks - الرتب المتاحة
/help - المساعدة

━━━━━━━━━━━━━━━━
🎯 كيفية الشراء:
1️⃣ اضغط على /buy
2️⃣ اختر المنتج والسعر
3️⃣ ادفع بنجوم تيليجرام ⭐
4️⃣ استمتع بامتلاك اللاشيء!

💡 نصيحة: كلما زاد إنفاقك، ارتفعت رتبتك!"""
    
    await update.message.reply_text(help_text)

async def ranks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ranks_text = """╔══════════════════════╗
║   🏆 الرتب المتاحة   ║
╚══════════════════════╝

"""
    
    for i, (threshold, title) in enumerate(RANKS, 1):
        if threshold == 0:
            ranks_text += f"{i}. {title}\n   البداية: 0 ⭐\n\n"
        else:
            ranks_text += f"{i}. {title}\n   المطلوب: {threshold:,} ⭐\n\n"
    
    ranks_text += """━━━━━━━━━━━━━━━━
💪 ابدأ رحلتك الآن!
استخدم /buy للشراء"""
    
    await update.message.reply_text(ranks_text)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء العام"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # إرسال رسالة للأدمن في حالة الأخطاء الكبيرة
    if ADMIN_ID and isinstance(update, Update):
        try:
            error_msg = f"⚠️ خطأ:\n{str(context.error)[:500]}"
            await context.bot.send_message(ADMIN_ID, error_msg)
        except:
            pass

def main():
    """تشغيل البوت"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير موجود!")
        return
    
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالج الأخطاء
    app.add_error_handler(error_handler)
    
    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ranks", ranks_command))
    app.add_handler(CallbackQueryHandler(handle_buy_callback, pattern="^buy_"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    logger.info("🚀 البوت يعمل الآن...")
    logger.info(f"📁 ملف الطلبات: {ORDERS_FILE}")
    
    # معالجة الإيقاف النظيف
    def signal_handler(sig, frame):
        logger.info("\n⏸️ إيقاف البوت...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # تشغيل البوت
    try:
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("⏸️ تم إيقاف البوت")
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()
