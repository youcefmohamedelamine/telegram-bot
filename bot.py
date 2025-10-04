import logging
import json
import os
import signal
import sys
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
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
from telegram.error import TelegramError, NetworkError, TimedOut, BadRequest

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

# ============= مدير الطلبات المحصن =============
class OrderManager:
    def __init__(self, filename: str, backup_filename: str):
        self.filename = filename
        self.backup_filename = backup_filename
        self.orders = self._load()
        self._create_backup()
    
    def _validate_structure(self, data: Any) -> bool:
        """التحقق من صحة بنية البيانات"""
        if not isinstance(data, dict):
            return False
        
        for user_id, user_data in data.items():
            if not isinstance(user_id, str):
                return False
            if not isinstance(user_data, dict):
                return False
            if "history" not in user_data:
                return False
            if not isinstance(user_data["history"], list):
                return False
        
        return True
    
    def _load(self) -> Dict:
        """تحميل الطلبات مع معالجة شاملة للأخطاء"""
        try:
            # محاولة تحميل الملف الأساسي
            if os.path.exists(self.filename):
                with open(self.filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if self._validate_structure(data):
                        logger.info(f"✅ تم تحميل {len(data)} مستخدم من الملف الأساسي")
                        return data
                    else:
                        logger.warning("⚠️ بنية الملف الأساسي غير صحيحة")
        except json.JSONDecodeError as e:
            logger.error(f"❌ خطأ في قراءة JSON من الملف الأساسي: {e}")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الملف الأساسي: {e}")
        
        # محاولة تحميل النسخة الاحتياطية
        try:
            if os.path.exists(self.backup_filename):
                with open(self.backup_filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if self._validate_structure(data):
                        logger.info(f"✅ تم تحميل {len(data)} مستخدم من النسخة الاحتياطية")
                        # استعادة الملف الأساسي
                        self._save_to_file(self.filename, data)
                        return data
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل النسخة الاحتياطية: {e}")
        
        logger.info("📝 إنشاء قاعدة بيانات جديدة")
        return {}
    
    def _save_to_file(self, filename: str, data: Dict) -> bool:
        """حفظ البيانات إلى ملف محدد"""
        try:
            # الحفظ في ملف مؤقت أولاً
            temp_file = f"{filename}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # نقل الملف المؤقت إلى الملف الأصلي
            if os.path.exists(filename):
                os.replace(temp_file, filename)
            else:
                os.rename(temp_file, filename)
            
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الملف {filename}: {e}")
            # حذف الملف المؤقت إذا كان موجوداً
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
    
    def _create_backup(self):
        """إنشاء نسخة احتياطية"""
        if self.orders:
            self._save_to_file(self.backup_filename, self.orders)
    
    def save(self) -> bool:
        """حفظ الطلبات مع نسخة احتياطية"""
        success = self._save_to_file(self.filename, self.orders)
        if success:
            self._create_backup()
        return success
    
    def add_order(self, user_id: int, order_data: Dict) -> bool:
        """إضافة طلب جديد مع التحقق"""
        try:
            user_id = str(user_id)
            
            # التحقق من صحة البيانات
            if not isinstance(order_data, dict):
                logger.error("❌ بيانات الطلب ليست قاموساً")
                return False
            
            # التأكد من وجود الحقول المطلوبة
            required_fields = ["time", "amount", "category"]
            for field in required_fields:
                if field not in order_data:
                    logger.error(f"❌ حقل مفقود: {field}")
                    return False
            
            # التحقق من صحة القيم
            if not isinstance(order_data["amount"], int) or order_data["amount"] <= 0:
                logger.error("❌ مبلغ غير صحيح")
                return False
            
            if order_data["category"] not in PRODUCTS:
                logger.error("❌ فئة غير صحيحة")
                return False
            
            # إضافة الطلب
            if user_id not in self.orders:
                self.orders[user_id] = {"history": []}
            
            self.orders[user_id]["history"].append(order_data)
            
            # الحفظ
            return self.save()
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة الطلب: {e}")
            return False
    
    def get_total_spent(self, user_id: int) -> int:
        """الحصول على إجمالي الإنفاق مع معالجة الأخطاء"""
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
        except Exception as e:
            logger.error(f"❌ خطأ في حساب الإنفاق: {e}")
            return 0
    
    def get_order_count(self, user_id: int) -> int:
        """الحصول على عدد الطلبات مع معالجة الأخطاء"""
        try:
            user_id = str(user_id)
            if user_id not in self.orders:
                return 0
            return len(self.orders[user_id].get("history", []))
        except Exception as e:
            logger.error(f"❌ خطأ في حساب الطلبات: {e}")
            return 0
    
    def get_total_users(self) -> int:
        """الحصول على عدد المستخدمين"""
        try:
            return len(self.orders)
        except:
            return 0
    
    def get_total_revenue(self) -> int:
        """الحصول على الإيرادات الكلية"""
        try:
            total = 0
            for user_data in self.orders.values():
                for order in user_data.get("history", []):
                    amount = order.get("amount", 0)
                    if isinstance(amount, int) and amount > 0:
                        total += amount
            return total
        except Exception as e:
            logger.error(f"❌ خطأ في حساب الإيرادات: {e}")
            return 0

# ============= تهيئة مدير الطلبات =============
order_manager = OrderManager(ORDERS_FILE, ORDERS_BACKUP)

# ============= الدوال المساعدة =============
def get_user_title(total_spent: int) -> str:
    """الحصول على لقب المستخدم"""
    try:
        total_spent = int(total_spent)
        for threshold, title in RANKS:
            if total_spent >= threshold:
                return title
        return RANKS[-1][1]
    except:
        return RANKS[-1][1]

def validate_price(category: str, amount: int) -> bool:
    """التحقق من صحة السعر"""
    try:
        if category not in VALID_PRICES:
            return False
        return amount in VALID_PRICES[category]
    except:
        return False

def sanitize_text(text: str, max_length: int = 100) -> str:
    """تنظيف النص من المدخلات الخطرة"""
    try:
        if not isinstance(text, str):
            return "Unknown"
        
        # إزالة المحارف الخاصة الخطرة
        text = text.strip()[:max_length]
        
        # إزالة أي HTML أو markdown خطير
        dangerous_chars = ['<', '>', '{', '}', '`', '\\']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        return text if text else "Unknown"
    except:
        return "Unknown"

async def safe_reply(update: Update, text: str, **kwargs) -> bool:
    """إرسال رسالة مع معالجة الأخطاء"""
    try:
        if update.message:
            await update.message.reply_text(text, **kwargs)
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, **kwargs)
        return True
    except BadRequest as e:
        logger.error(f"❌ طلب خاطئ: {e}")
        return False
    except TimedOut:
        logger.error("⏱️ انتهى الوقت")
        return False
    except NetworkError as e:
        logger.error(f"🌐 خطأ في الشبكة: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطأ في الإرسال: {e}")
        return False

# ============= معالجات الأوامر =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start المحصن"""
    try:
        if not update.message or not update.message.from_user:
            logger.error("❌ رسالة أو مستخدم غير موجود")
            return
        
        user = update.message.from_user
        user_id = str(user.id)
        
        # معالجة deep link للشراء المباشر
        if context.args and len(context.args) > 0:
            try:
                arg = str(context.args[0])
                if arg.startswith('buy_'):
                    parts = arg.split('_')
                    if len(parts) >= 3:
                        category = parts[1]
                        amount = int(parts[2])
                        
                        # التحقق من صحة البيانات
                        if category not in PRODUCTS:
                            await safe_reply(update, "❌ منتج غير صحيح")
                            return
                        
                        if not validate_price(category, amount):
                            await safe_reply(update, "❌ سعر غير صحيح")
                            return
                        
                        product = PRODUCTS[category]
                        prices = [LabeledPrice(product["name"], amount)]
                        
                        # إرسال الفاتورة مباشرة
                        try:
                            await update.message.reply_invoice(
                                title=f"{product['emoji']} {product['name']}",
                                description=f"{product['desc']}\n💰 السعر: {amount:,} نجمة ⭐",
                                payload=f"order_{user_id}_{category}_{amount}_{datetime.now().timestamp()}",
                                provider_token=PROVIDER_TOKEN,
                                currency="XTR",
                                prices=prices,
                                need_name=False,
                                need_phone_number=False,
                                need_email=False,
                                need_shipping_address=False,
                                is_flexible=False
                            )
                            logger.info(f"✅ تم إرسال فاتورة: {category} - {amount}")
                            return
                        except Exception as invoice_error:
                            logger.error(f"❌ خطأ في إرسال الفاتورة: {invoice_error}")
                            await safe_reply(update, "❌ خطأ في إنشاء الفاتورة. تأكد من تفعيل Telegram Stars في إعدادات البوت")
                            return
                            
            except ValueError as e:
                logger.error(f"❌ خطأ في معالجة المبلغ: {e}")
                await safe_reply(update, "❌ حدث خطأ في إنشاء الفاتورة")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة deep link: {e}")
                await safe_reply(update, "❌ حدث خطأ، حاول مرة أخرى")
                return
        
        # الحصول على بيانات المستخدم
        total_spent = order_manager.get_total_spent(user_id)
        user_title = get_user_title(total_spent)
        order_count = order_manager.get_order_count(user_id)
        
        # إعداد بيانات Web App
        user_data = {
            "totalSpent": total_spent,
            "orderCount": order_count,
            "rank": user_title
        }
        
        import base64
        try:
            encoded_data = base64.b64encode(json.dumps(user_data).encode()).decode()
            web_url = f"{WEB_APP_URL}?startapp={encoded_data}"
        except Exception as e:
            logger.error(f"❌ خطأ في تشفير البيانات: {e}")
            web_url = WEB_APP_URL
        
        keyboard = [[InlineKeyboardButton("🛍️ افتح المتجر", web_app={"url": web_url})]]
        
        first_name = sanitize_text(user.first_name, 50)
        
        welcome = f"""╔══════════════════════╗
║   🌟 متجر اللاشيء 🌟   ║
╚══════════════════════╝

مرحباً يا {first_name} 👋

{user_title}

━━━━━━━━━━━━━━━━
💰 إجمالي إنفاقك: {total_spent:,} ⭐
📦 عدد طلباتك: {order_count}
━━━━━━━━━━━━━━━━

🎭 اضغط الزر أدناه لفتح المتجر
أو استخدم الأمر:
/buy لعرض المنتجات"""
        
        await safe_reply(update, welcome, reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالج start: {e}")
        await safe_reply(update, "❌ حدث خطأ، حاول مرة أخرى لاحقاً")

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /buy المحصن"""
    try:
        if not update.message:
            return
        
        keyboard = []
        
        # بناء لوحة المفاتيح بشكل آمن
        for category, prices in VALID_PRICES.items():
            row = []
            product = PRODUCTS.get(category)
            if product:
                for price in prices:
                    label = f"{product['emoji']} {price//1000}K ⭐"
                    row.append(InlineKeyboardButton(
                        label,
                        callback_data=f"buy_{category}_{price}"
                    ))
                keyboard.append(row)
        
        text = """🛍️ اختر المنتج والسعر:

🔹 لاشيء صغير - مثالي للمبتدئين
🔷 لاشيء متوسط - الأكثر شعبية  
💠 لاشيء كبير - للمحترفين فقط"""
        
        await safe_reply(update, text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالج buy: {e}")
        await safe_reply(update, "❌ حدث خطأ، حاول /start")

async def handle_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج callback الشراء المحصن"""
    try:
        query = update.callback_query
        if not query or not query.message or not query.from_user:
            return
        
        await query.answer()
        
        user = query.from_user
        user_id = str(user.id)
        
        # معالجة البيانات بشكل آمن
        parts = str(query.data).split('_')
        if len(parts) < 3:
            await query.message.reply_text("❌ بيانات غير صحيحة")
            return
        
        category = parts[1]
        try:
            amount = int(parts[2])
        except ValueError:
            await query.message.reply_text("❌ مبلغ غير صحيح")
            return
        
        # التحقق من صحة البيانات
        if category not in PRODUCTS:
            await query.message.reply_text("❌ منتج غير صحيح")
            return
        
        if not validate_price(category, amount):
            await query.message.reply_text("❌ سعر غير صحيح")
            return
        
        product = PRODUCTS[category]
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
        logger.error(f"❌ خطأ في معالج callback: {e}")
        try:
            await query.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
        except:
            pass

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج التحقق قبل الدفع"""
    try:
        query = update.pre_checkout_query
        if query:
            await query.answer(ok=True)
    except Exception as e:
        logger.error(f"❌ خطأ في precheckout: {e}")
        try:
            await query.answer(ok=False, error_message="حدث خطأ، حاول مرة أخرى")
        except:
            pass

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الدفع الناجح المحصن"""
    try:
        if not update.message or not update.message.from_user or not update.message.successful_payment:
            logger.error("❌ بيانات الدفع غير كاملة")
            return
        
        user = update.message.from_user
        user_id = str(user.id)
        payment = update.message.successful_payment
        
        # معالجة payload بشكل آمن
        try:
            payload_parts = str(payment.invoice_payload).split("_")
            category = payload_parts[2] if len(payload_parts) > 2 else "unknown"
        except:
            category = "unknown"
        
        # التحقق من صحة الفئة
        product = PRODUCTS.get(category)
        if not product:
            product = {"name": "لاشيء", "emoji": "✨", "desc": ""}
            logger.warning(f"⚠️ فئة غير معروفة: {category}")
        
        # إعداد بيانات الطلب
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
        
        # حفظ الطلب
        save_success = order_manager.add_order(user_id, order_data)
        if not save_success:
            logger.error("❌ فشل حفظ الطلب")
        
        # حساب الترقية
        total_spent = order_manager.get_total_spent(user_id)
        old_total = max(0, total_spent - payment.total_amount)
        old_title = get_user_title(old_total)
        new_title = get_user_title(total_spent)
        
        rank_up = ""
        if old_title != new_title:
            rank_up = f"\n\n🎊 تهانينا! ترقية اللقب!\n{old_title} ➜ {new_title}"
        
        success = f"""╔══════════════════════╗
║   🎉 تم الدفع بنجاح! 🎉   ║
╚══════════════════════╝

عزيزي {first_name}،

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
        
        await safe_reply(update, success)
        
        # إشعار الأدمن
        if ADMIN_ID:
            try:
                admin_msg = f"""╔══════════════════════╗
║   📢 طلب جديد!   ║
╚══════════════════════╝

👤 المستخدم: @{username}
🆔 ID: {user.id}
📛 الاسم: {first_name}
🏷️ اللقب: {new_title}

📦 المنتج: {product['name']}
💰 المبلغ: {payment.total_amount:,} ⭐
💎 الإجمالي: {total_spent:,} ⭐

🕐 الوقت: {datetime.now().strftime("%Y-%m-%d %H:%M")}"""
                
                await context.bot.send_message(ADMIN_ID, admin_msg)
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال إشعار الأدمن: {e}")
    
    except Exception as e:
        logger.error(f"❌ خطأ خطير في successful_payment: {e}")
        try:
            await safe_reply(update, "✅ تم الدفع بنجاح!\n⚠️ حدث خطأ في حفظ البيانات، تواصل مع الدعم")
        except:
            pass

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /stats المحصن"""
    try:
        if not update.message or not update.message.from_user:
            return
        
        user = update.message.from_user
        user_id = str(user.id)
        
        # إحصائيات الأدمن
        if ADMIN_ID and str(user.id) == ADMIN_ID:
            total_users = order_manager.get_total_users()
            total_revenue = order_manager.get_total_revenue()
            
            admin_stats = f"""╔══════════════════════╗
║   📊 إحصائيات عامة   ║
╚══════════════════════╝

👥 إجمالي المستخدمين: {total_users}
💰 إجمالي الإيرادات: {total_revenue:,} ⭐

━━━━━━━━━━━━━━━━"""
            await safe_reply(update, admin_stats)
        
        # إحصائيات المستخدم
        total_spent = order_manager.get_total_spent(user_id)
        order_count = order_manager.get_order_count(user_id)
        user_title = get_user_title(total_spent)
        
        # حساب الترقية القادمة
        next_rank_info = ""
        for threshold, title in RANKS:
            if total_spent < threshold:
                remaining = threshold - total_spent
                progress = min(100, (total_spent / threshold) * 100)
                next_rank_info = f"\n\n📊 التقدم للرتبة القادمة:\n{title}\n🎯 المتبقي: {remaining:,} ⭐\n📈 التقدم: {progress:.1f}%"
                break
        
        if not next_rank_info:
            next_rank_info = "\n\n🏆 تهانينا! وصلت لأعلى رتبة!"
        
        first_name = sanitize_text(user.first_name, 50)
        avg_order = (total_spent // order_count) if order_count > 0 else 0
        
        stats = f"""╔══════════════════════╗
║   📊 إحصائياتك   ║
╚══════════════════════╝

👤 الاسم: {first_name}
🏷️ اللقب: {user_title}

━━━━━━━━━━━━━━━━
💰 إجمالي الإنفاق: {total_spent:,} ⭐
📦 عدد الطلبات: {order_count}
💵 متوسط الطلب: {avg_order:,} ⭐{next_rank_info}

━━━━━━━━━━━━━━━━
استخدم /buy للتسوق الآن!"""
        
        await safe_reply(update, stats)
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالج stats: {e}")
        await safe_reply(update, "❌ حدث خطأ في عرض الإحصائيات")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /help المحصن"""
    try:
        if not update.message:
            return
        
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
        
        await safe_reply(update, help_text)
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالج help: {e}")
        await safe_reply(update, "❌ حدث خطأ")

async def ranks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /ranks المحصن"""
    try:
        if not update.message:
            return
        
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
        
        await safe_reply(update, ranks_text)
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالج ranks: {e}")
        await safe_reply(update, "❌ حدث خطأ")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء العام المحسن"""
    try:
        logger.error(f"❌ Exception while handling update: {context.error}", exc_info=context.error)
        
        # إرسال رسالة للأدمن في حالة الأخطاء الكبيرة
        if ADMIN_ID and isinstance(update, Update):
            try:
                error_text = str(context.error)[:500]
                error_msg = f"⚠️ خطأ في البوت:\n\n{error_text}\n\nالوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                await context.bot.send_message(ADMIN_ID, error_msg)
            except Exception as e:
                logger.error(f"❌ فشل إرسال إشعار الخطأ للأدمن: {e}")
        
        # محاولة إرسال رسالة للمستخدم
        if isinstance(update, Update):
            try:
                if update.message:
                    await update.message.reply_text(
                        "❌ عذراً، حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.\n"
                        "إذا استمرت المشكلة، تواصل مع الدعم."
                    )
                elif update.callback_query:
                    await update.callback_query.message.reply_text(
                        "❌ عذراً، حدث خطأ. حاول مرة أخرى."
                    )
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ خطأ في معالج الأخطاء نفسه: {e}")

async def post_init(application: Application):
    """إعدادات بعد التهيئة"""
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ البوت متصل: @{bot_info.username}")
        logger.info(f"📊 عدد المستخدمين المسجلين: {order_manager.get_total_users()}")
        logger.info(f"💰 إجمالي الإيرادات: {order_manager.get_total_revenue():,} ⭐")
    except Exception as e:
        logger.error(f"❌ خطأ في post_init: {e}")

async def shutdown(application: Application):
    """معالج الإيقاف النظيف"""
    try:
        logger.info("⏸️ جاري إيقاف البوت...")
        
        # حفظ البيانات قبل الإيقاف
        order_manager.save()
        logger.info("💾 تم حفظ البيانات")
        
        # إشعار الأدمن
        if ADMIN_ID:
            try:
                await application.bot.send_message(
                    ADMIN_ID,
                    f"⏸️ تم إيقاف البوت\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except:
                pass
        
        logger.info("✅ تم إيقاف البوت بنجاح")
    except Exception as e:
        logger.error(f"❌ خطأ في shutdown: {e}")

def validate_config() -> bool:
    """التحقق من الإعدادات قبل التشغيل"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("❌ BOT_TOKEN غير موجود")
    elif len(BOT_TOKEN) < 40:
        errors.append("❌ BOT_TOKEN غير صحيح")
    
    if ADMIN_ID and not ADMIN_ID.isdigit():
        errors.append("⚠️ ADMIN_ID يجب أن يكون رقماً")
    
    if not WEB_APP_URL.startswith(("http://", "https://")):
        errors.append("⚠️ WEB_APP_URL يجب أن يبدأ بـ http:// أو https://")
    
    if errors:
        for error in errors:
            logger.error(error)
        return False
    
    return True

def main():
    """دالة التشغيل الرئيسية المحصنة"""
    try:
        # التحقق من الإعدادات
        if not validate_config():
            logger.error("❌ فشل التحقق من الإعدادات!")
            sys.exit(1)
        
        logger.info("🔧 إنشاء التطبيق...")
        
        # إنشاء التطبيق مع إعدادات محسنة
        app = Application.builder()\
            .token(BOT_TOKEN)\
            .connect_timeout(30)\
            .read_timeout(30)\
            .write_timeout(30)\
            .get_updates_connect_timeout(30)\
            .get_updates_read_timeout(30)\
            .post_init(post_init)\
            .post_shutdown(shutdown)\
            .build()
        
        # إضافة معالج الأخطاء العام
        app.add_error_handler(error_handler)
        
        # إضافة المعالجات
        logger.info("📝 تسجيل المعالجات...")
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("buy", buy_command))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("ranks", ranks_command))
        app.add_handler(CallbackQueryHandler(handle_buy_callback, pattern="^buy_"))
        app.add_handler(PreCheckoutQueryHandler(precheckout))
        app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
        
        logger.info("=" * 50)
        logger.info("🚀 البوت يعمل الآن...")
        logger.info(f"📁 ملف الطلبات: {ORDERS_FILE}")
        logger.info(f"💾 ملف النسخ الاحتياطي: {ORDERS_BACKUP}")
        logger.info(f"👤 Admin ID: {ADMIN_ID if ADMIN_ID else 'غير محدد'}")
        logger.info("=" * 50)
        
        # معالجة الإيقاف النظيف
        def signal_handler(sig, frame):
            logger.info("\n⏸️ تم استقبال إشارة الإيقاف...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # تشغيل البوت مع معالجة الأخطاء
        try:
            app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
        except KeyboardInterrupt:
            logger.info("⏸️ تم إيقاف البوت بواسطة المستخدم")
        except NetworkError as e:
            logger.error(f"🌐 خطأ في الشبكة: {e}")
            logger.info("🔄 حاول إعادة تشغيل البوت")
        except Exception as e:
            logger.error(f"❌ خطأ خطير: {e}", exc_info=True)
            
    except Exception as e:
        logger.error(f"❌ فشل تشغيل البوت: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
