import logging
import json
import os
import signal
import sys
import requests
from datetime import datetime
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters
)
from telegram.error import NetworkError, BadRequest

# ============= إعدادات البيئة =============
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
PROVIDER_TOKEN = "XTR"
ORDERS_FILE = "orders.json"
ORDERS_BACKUP = "orders_backup.json"
WEB_APP_URL = "https://youcefmohamedelamine.github.io/winter_land_bot/"

# ============= إعدادات السجلات =============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ============= البيانات الثابتة =============
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

VALID_PRICES = {
    "small": [5000, 10000, 15000],
    "medium": [20000, 30000, 40000],
    "large": [50000, 75000, 100000]
}

# ============= مدير الطلبات =============
class OrderManager:
    def __init__(self, filename: str, backup_filename: str):
        self.filename = filename
        self.backup_filename = backup_filename
        self.orders = self._load()
        self._create_backup()
    
    def _validate_structure(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        for user_id, user_data in data.items():
            if not isinstance(user_id, str) or not isinstance(user_data, dict):
                return False
            if "history" not in user_data or not isinstance(user_data["history"], list):
                return False
        return True
    
    def _load(self) -> Dict:
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if self._validate_structure(data):
                        logger.info(f"✅ تحميل {len(data)} مستخدم")
                        return data
        except Exception as e:
            logger.error(f"❌ خطأ تحميل: {e}")
        
        try:
            if os.path.exists(self.backup_filename):
                with open(self.backup_filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if self._validate_structure(data):
                        self._save_to_file(self.filename, data)
                        return data
        except:
            pass
        
        logger.info("📝 قاعدة بيانات جديدة")
        return {}
    
    def _save_to_file(self, filename: str, data: Dict) -> bool:
        try:
            temp_file = f"{filename}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            if os.path.exists(filename):
                os.replace(temp_file, filename)
            else:
                os.rename(temp_file, filename)
            return True
        except Exception as e:
            logger.error(f"❌ خطأ حفظ: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
    
    def _create_backup(self):
        if self.orders:
            self._save_to_file(self.backup_filename, self.orders)
    
    def save(self) -> bool:
        success = self._save_to_file(self.filename, self.orders)
        if success:
            self._create_backup()
        return success
    
    def add_order(self, user_id: int, order_data: Dict) -> bool:
        try:
            user_id = str(user_id)
            if not isinstance(order_data, dict):
                return False
            
            required = ["time", "amount", "category"]
            if not all(f in order_data for f in required):
                return False
            
            if not isinstance(order_data["amount"], int) or order_data["amount"] <= 0:
                return False
            
            if order_data["category"] not in PRODUCTS:
                return False
            
            if user_id not in self.orders:
                self.orders[user_id] = {"history": []}
            
            self.orders[user_id]["history"].append(order_data)
            return self.save()
        except Exception as e:
            logger.error(f"❌ خطأ إضافة طلب: {e}")
            return False
    
    def get_total_spent(self, user_id: int) -> int:
        try:
            user_id = str(user_id)
            if user_id not in self.orders:
                return 0
            total = 0
            for order in self.orders[user_id].get("history", []):
                amount = order.get("amount", 0)
                if isinstance(amount, int) and amount > 0:
                    total += amount
            return total
        except:
            return 0
    
    def get_order_count(self, user_id: int) -> int:
        try:
            user_id = str(user_id)
            if user_id not in self.orders:
                return 0
            return len(self.orders[user_id].get("history", []))
        except:
            return 0
    
    def get_total_users(self) -> int:
        return len(self.orders)
    
    def get_total_revenue(self) -> int:
        try:
            total = 0
            for user_data in self.orders.values():
                for order in user_data.get("history", []):
                    amount = order.get("amount", 0)
                    if isinstance(amount, int) and amount > 0:
                        total += amount
            return total
        except:
            return 0

order_manager = OrderManager(ORDERS_FILE, ORDERS_BACKUP)

# ============= الدوال المساعدة =============
def get_user_title(total_spent: int) -> str:
    try:
        total_spent = int(total_spent)
        for threshold, title in RANKS:
            if total_spent >= threshold:
                return title
        return RANKS[-1][1]
    except:
        return RANKS[-1][1]

def validate_price(category: str, amount: int) -> bool:
    try:
        if category not in VALID_PRICES:
            return False
        return amount in VALID_PRICES[category]
    except:
        return False

def sanitize_text(text: str, max_length: int = 100) -> str:
    try:
        if not isinstance(text, str):
            return "Unknown"
        text = text.strip()[:max_length]
        dangerous_chars = ['<', '>', '{', '}', '`', '\\']
        for char in dangerous_chars:
            text = text.replace(char, '')
        return text if text else "Unknown"
    except:
        return "Unknown"

# ============= معالج واحد فقط: /start =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.from_user:
            return
        
        user = update.message.from_user
        user_id = str(user.id)
        
        # معالجة deep link للشراء من Web App
        if context.args and len(context.args) > 0:
            try:
                arg = str(context.args[0])
                if arg.startswith('buy_'):
                    parts = arg.split('_')
                    if len(parts) >= 3:
                        category = parts[1]
                        amount = int(parts[2])
                        
                        if category not in PRODUCTS or not validate_price(category, amount):
                            await update.message.reply_text("❌ بيانات غير صحيحة")
                            return
                        
                        product = PRODUCTS[category]
                        prices = [LabeledPrice(label="السعر", amount=amount)]
                        
                        description = f"""✨ {product['desc']}

🎁 ستحصل على:
• ملكية حصرية للاشيء
• ترقية اللقب التلقائية
• دعم فني مميز

💫 شكراً لاختيارك متجر اللاشيء!"""
                        
                        await update.message.reply_invoice(
                            title=f"{product['name']}",
                            description=description,
                            payload=f"order_{user_id}_{category}_{amount}_{datetime.now().timestamp()}",
                            provider_token=PROVIDER_TOKEN,
                            currency="XTR",
                            prices=prices,
                            max_tip_amount=50000,
                            suggested_tip_amounts=[1000, 5000, 10000, 25000],
                            need_name=False,
                            need_phone_number=False,
                            need_email=False,
                            need_shipping_address=False,
                            is_flexible=False
                        )
                        logger.info(f"✅ فاتورة: {category} - {amount}")
                        return
                        logger.info(f"✅ فاتورة: {category} - {amount}")
                        return
            except Exception as e:
                logger.error(f"❌ خطأ deep link: {e}")
        
        # الحصول على بيانات المستخدم
        total_spent = order_manager.get_total_spent(user_id)
        user_title = get_user_title(total_spent)
        order_count = order_manager.get_order_count(user_id)
        
        # إعداد Web App URL مع البيانات
        user_data = {
            "totalSpent": total_spent,
            "orderCount": order_count,
            "rank": user_title
        }
        
        import base64
        try:
            encoded_data = base64.b64encode(json.dumps(user_data).encode()).decode()
            web_url = f"{WEB_APP_URL}?startapp={encoded_data}"
        except:
            web_url = WEB_APP_URL
        
        # زر واحد فقط: افتح المتجر
        keyboard = [[InlineKeyboardButton("🛍️ افتح المتجر", web_app=WebAppInfo(url=web_url))]]
        
        first_name = sanitize_text(user.first_name, 50)
        
        welcome = f"""🌟 متجر اللاشيء 🌟

مرحباً {first_name} 👋

{user_title}

💰 إنفاقك: {total_spent:,} ⭐
📦 طلباتك: {order_count}

اضغط الزر للدخول للمتجر 👇"""
        
        await update.message.reply_text(
            welcome, 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ start: {e}")

# ============= معالج الدفع =============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.pre_checkout_query
        if query:
            await query.answer(ok=True)
    except Exception as e:
        logger.error(f"❌ خطأ precheckout: {e}")

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.from_user or not update.message.successful_payment:
            return
        
        user = update.message.from_user
        user_id = str(user.id)
        payment = update.message.successful_payment
        
        try:
            payload_parts = str(payment.invoice_payload).split("_")
            category = payload_parts[2] if len(payload_parts) > 2 else "unknown"
        except:
            category = "unknown"
        
        product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨", "desc": ""})
        
        username = sanitize_text(user.username if user.username else "Unknown", 50)
        first_name = sanitize_text(user.first_name, 50)
        
        order_data = {
            "time": datetime.now().isoformat(),
            "amount": payment.total_amount,
            "category": category,
            "product": product["name"],
            "username": username,
            "user_id": user.id
        }
        
        order_manager.add_order(user_id, order_data)
        
        total_spent = order_manager.get_total_spent(user_id)
        old_total = max(0, total_spent - payment.total_amount)
        old_title = get_user_title(old_total)
        new_title = get_user_title(total_spent)
        
        rank_up = ""
        if old_title != new_title:
            rank_up = f"\n\n🎊 ترقية!\n{old_title} ➜ {new_title}"
        
        success = f"""✅ تم الدفع بنجاح!

📦 المنتج: {product['name']}
💰 المبلغ: {payment.total_amount:,} ⭐

🏷️ لقبك: {new_title}
💎 إجمالي: {total_spent:,} ⭐{rank_up}

شكراً لك! 💫"""
        
        await update.message.reply_text(success)
        
        # إشعار الأدمن
        if ADMIN_ID:
            try:
                admin_msg = f"""📢 طلب جديد!

👤 @{username}
🆔 {user.id}
📛 {first_name}

📦 {product['name']}
💰 {payment.total_amount:,} ⭐
💎 الإجمالي: {total_spent:,} ⭐"""
                
                await context.bot.send_message(ADMIN_ID, admin_msg)
            except:
                pass
    
    except Exception as e:
        logger.error(f"❌ خطأ payment: {e}")

# ============= معالج الأخطاء =============
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ خطأ: {context.error}")

async def post_init(application: Application):
    try:
        # حذف webhook قبل البدء
        webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
        try:
            response = requests.get(webhook_url, timeout=10)
            if response.status_code == 200:
                logger.info("✅ تم حذف webhook")
        except:
            pass
        
        bot_info = await application.bot.get_me()
        logger.info(f"✅ البوت: @{bot_info.username}")
        logger.info(f"📊 المستخدمين: {order_manager.get_total_users()}")
        logger.info(f"💰 الإيرادات: {order_manager.get_total_revenue():,} ⭐")
    except Exception as e:
        logger.error(f"❌ خطأ init: {e}")

async def shutdown(application: Application):
    try:
        order_manager.save()
        logger.info("✅ تم إيقاف البوت")
    except:
        pass

def validate_config() -> bool:
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN غير صحيح")
        return False
    if ADMIN_ID and not ADMIN_ID.isdigit():
        logger.error("⚠️ ADMIN_ID يجب أن يكون رقماً")
    if not WEB_APP_URL.startswith(("http://", "https://")):
        logger.error("⚠️ WEB_APP_URL غير صحيح")
        return False
    return True

def main():
    try:
        if not validate_config():
            sys.exit(1)
        
        logger.info("🔧 تهيئة البوت...")
        
        app = Application.builder()\
            .token(BOT_TOKEN)\
            .connect_timeout(30)\
            .read_timeout(30)\
            .write_timeout(30)\
            .post_init(post_init)\
            .post_shutdown(shutdown)\
            .build()
        
        app.add_error_handler(error_handler)
        
        # معالج واحد فقط!
        app.add_handler(CommandHandler("start", start))
        app.add_handler(PreCheckoutQueryHandler(precheckout))
        app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
        
        logger.info("=" * 50)
        logger.info("🚀 البوت يعمل - كل شيء عبر Web App")
        logger.info("=" * 50)
        
        def signal_handler(sig, frame):
            logger.info("\n⏸️ إيقاف...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
            
    except Exception as e:
        logger.error(f"❌ فشل: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
