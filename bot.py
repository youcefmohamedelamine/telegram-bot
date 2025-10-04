import logging
import json
import os
import sys
import signal
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Dict, Any

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
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()
PORT = int(os.getenv("PORT", 8080))
WEB_APP_URL = "https://youcefmohamedelamine.github.io/winter_land_bot/"

# 🛡️ حماية 15: التحقق من ADMIN_ID
if ADMIN_ID:
    try:
        ADMIN_ID = int(ADMIN_ID)
        if not (0 < ADMIN_ID <= 9999999999):
            logging.error("❌ ADMIN_ID غير صالح")
            ADMIN_ID = None
    except ValueError:
        logging.error("❌ ADMIN_ID ليس رقماً")
        ADMIN_ID = None

# تكوين Logging متقدم
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
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

# ============= 🛡️ Rate Limiter (حماية 1-3, 17) =============
class RateLimiter:
    """
    🛡️ الحماية من:
    1. DDoS attacks
    2. Spam من مستخدم واحد
    3. استنزاف موارد السيرفر
    17. Memory Leak
    """
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            'command': (5, 60),
            'purchase': (3, 300),
            'webapp': (10, 60),
        }
        self.blocked_users = {}
        self.last_cleanup = datetime.now()
    
    async def cleanup_old_data(self):
        """🛡️ حماية 17: تنظيف البيانات القديمة"""
        now = datetime.now()
        if (now - self.last_cleanup).total_seconds() < 600:
            return
        
        for key in list(self.requests.keys()):
            cutoff = now - timedelta(seconds=600)
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
            if not self.requests[key]:
                del self.requests[key]
        
        for uid in list(self.blocked_users.keys()):
            if now > self.blocked_users[uid]:
                del self.blocked_users[uid]
        
        self.last_cleanup = now
        logger.info(f"🧹 تنظيف: {len(self.requests)} مفاتيح نشطة")
    
    def is_blocked(self, user_id: int) -> bool:
        if user_id in self.blocked_users:
            if datetime.now() < self.blocked_users[user_id]:
                return True
            else:
                del self.blocked_users[user_id]
        return False
    
    def block_user(self, user_id: int, minutes: int = 10):
        self.blocked_users[user_id] = datetime.now() + timedelta(minutes=minutes)
        logger.warning(f"🚫 حظر مؤقت: {user_id} لمدة {minutes} دقيقة")
    
    async def check_limit(self, user_id: int, action: str = 'command') -> bool:
        await self.cleanup_old_data()
        
        if self.is_blocked(user_id):
            return False
        
        now = datetime.now()
        max_requests, window = self.limits.get(action, (5, 60))
        
        cutoff = now - timedelta(seconds=window)
        key = f"{user_id}_{action}"
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
        
        if len(self.requests[key]) >= max_requests:
            logger.warning(f"⚠️ تجاوز الحد: {user_id} - {action}")
            if len(self.requests[key]) >= max_requests * 2:
                self.block_user(user_id)
            return False
        
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

# ============= 🛡️ Input Validator (حماية 4-5, 16) =============
class InputValidator:
    """
    🛡️ الحماية من:
    4. SQL Injection
    5. Invalid data types
    16. Log Injection
    """
    @staticmethod
    def validate_user_id(user_id: Any) -> Optional[int]:
        try:
            uid = int(user_id)
            if 0 < uid <= 9999999999:
                return uid
        except (ValueError, TypeError):
            pass
        logger.error(f"❌ user_id غير صالح: {user_id}")
        return None
    
    @staticmethod
    def validate_amount(amount: Any) -> Optional[int]:
        try:
            amt = int(amount)
            if 0 < amt <= 1000000:
                return amt
        except (ValueError, TypeError):
            pass
        logger.error(f"❌ مبلغ غير صالح: {amount}")
        return None
    
    @staticmethod
    def validate_category(category: Any) -> Optional[str]:
        if isinstance(category, str) and category in PRODUCTS:
            return category
        logger.error(f"❌ فئة غير صالحة: {category}")
        return None
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 100) -> str:
        """🛡️ حماية 16: تنظيف من Log Injection"""
        if not isinstance(text, str):
            return ""
        dangerous = ['<', '>', '"', "'", ';', '--', '/*', '*/', '\n', '\r', '\t']
        for char in dangerous:
            text = text.replace(char, '')
        return text[:max_length].strip()

validator = InputValidator()

# ============= 🛡️ Order Lock (حماية 14) =============
class OrderLock:
    """🛡️ حماية 14: منع الطلبات المتزامنة"""
    def __init__(self):
        self.locks = {}
    
    def get_lock(self, user_id: int):
        if user_id not in self.locks:
            self.locks[user_id] = asyncio.Lock()
        return self.locks[user_id]

order_lock = OrderLock()

# ============= 🛡️ مدير الطلبات المحمي (حماية 6-8, 13, 19) =============
class OrderManager:
    """
    🛡️ الحماية من:
    6. Race conditions
    7. Database connection loss
    8. Transaction failures
    13. Integer Overflow
    19. Database Pool Exhaustion
    """
    def __init__(self):
        self.pool = None
        self.max_retries = 3
        self.retry_delay = 1
    
    async def connect(self):
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL غير موجود")
            sys.exit(1)
        
        for attempt in range(self.max_retries):
            try:
                self.pool = await asyncpg.create_pool(
                    DATABASE_URL,
                    min_size=2,
                    max_size=10,
                    max_inactive_connection_lifetime=300,
                    command_timeout=60,
                    timeout=30  # 🛡️ حماية 19
                )
                logger.info("✅ اتصال PostgreSQL")
                await self.create_table()
                return
            except Exception as e:
                logger.error(f"❌ محاولة {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error("❌ فشل الاتصال بقاعدة البيانات")
                    sys.exit(1)

    async def create_table(self):
        """إنشاء/تحديث جدول users بأمان"""
        try:
            # الجدول الأساسي
            await self.pool.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    total_spent BIGINT DEFAULT 0 CHECK (total_spent >= 0),
                    order_count INT DEFAULT 0 CHECK (order_count >= 0),
                    rank TEXT NOT NULL DEFAULT 'زائر جديد 🌱',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إضافة الأعمدة الجديدة بأمان
            await self.pool.execute('''
                DO $$ 
                BEGIN
                    BEGIN
                        ALTER TABLE users ADD COLUMN last_purchase TIMESTAMP;
                    EXCEPTION 
                        WHEN duplicate_column THEN NULL;
                    END;
                    
                    BEGIN
                        ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE;
                    EXCEPTION 
                        WHEN duplicate_column THEN NULL;
                    END;
                END $$;
            ''')
            
            # تصحيح نوع last_purchase إذا كان TEXT
            await self.pool.execute('''
                DO $$ 
                BEGIN
                    ALTER TABLE users 
                    ALTER COLUMN last_purchase TYPE TIMESTAMP 
                    USING NULLIF(last_purchase, '')::timestamp;
                EXCEPTION 
                    WHEN OTHERS THEN NULL;
                END $$;
            ''')
            
            # الـ indexes
            await self.pool.execute('''
                CREATE INDEX IF NOT EXISTS idx_total_spent 
                ON users(total_spent DESC);
            ''')
            
            await self.pool.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_purchase 
                ON users(last_purchase DESC);
            ''')
            
            logger.info("✅ جدول users جاهز بالكامل")
        except Exception as e:
            logger.error(f"❌ فشل إنشاء الجدول: {e}", exc_info=True)
            raise

    async def execute_with_retry(self, query: str, *args, fetch: bool = False):
        for attempt in range(self.max_retries):
            try:
                async with self.pool.acquire() as conn:
                    if fetch:
                        return await conn.fetchrow(query, *args)
                    else:
                        return await conn.execute(query, *args)
            except asyncpg.PostgresError as e:
                logger.warning(f"⚠️ محاولة {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"❌ فشل الاستعلام: {query[:50]}")
                    raise

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        uid = validator.validate_user_id(user_id)
        if not uid:
            return None
        
        try:
            row = await self.execute_with_retry(
                """
                SELECT total_spent, order_count, rank, is_blocked 
                FROM users WHERE id = $1
                """,
                uid,
                fetch=True
            )
            
            if row:
                if row['is_blocked']:
                    logger.warning(f"🚫 مستخدم محظور: {uid}")
                    return None
                
                return {
                    "totalSpent": row['total_spent'],
                    "orderCount": row['order_count'],
                    "rank": row['rank']
                }
            
            initial_rank = get_rank(0)
            await self.execute_with_retry(
                """
                INSERT INTO users (id, total_spent, order_count, rank)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
                """,
                uid, 0, 0, initial_rank
            )
            
            return {"totalSpent": 0, "orderCount": 0, "rank": initial_rank}
            
        except Exception as e:
            logger.error(f"❌ خطأ get_user_data: {e}")
            return None

    async def add_order(self, user_id: int, amount: int, category: str) -> Optional[tuple]:
        uid = validator.validate_user_id(user_id)
        amt = validator.validate_amount(amount)
        cat = validator.validate_category(category)
        
        if not all([uid, amt, cat]):
            return None
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    row = await conn.fetchrow(
                        """
                        SELECT total_spent, is_blocked 
                        FROM users 
                        WHERE id = $1 
                        FOR UPDATE
                        """,
                        uid
                    )
                    
                    if not row:
                        logger.error(f"❌ مستخدم غير موجود: {uid}")
                        return None
                    
                    if row['is_blocked']:
                        logger.warning(f"🚫 محاولة شراء من مستخدم محظور: {uid}")
                        return None
                    
                    old_total = row['total_spent']
                    new_total = old_total + amt
                    
                    # 🛡️ حماية 13: Integer Overflow
                    if new_total > 9_000_000_000_000:
                        logger.error(f"❌ [{uid}] تجاوز الحد الأقصى: {new_total}")
                        return None
                    
                    new_rank = get_rank(new_total)
                    
                    await conn.execute(
                        """
                        UPDATE users 
                        SET total_spent = $2,
                            order_count = order_count + 1,
                            rank = $3,
                            last_purchase = CURRENT_TIMESTAMP
                        WHERE id = $1
                        """,
                        uid, new_total, new_rank
                    )
                    
                    logger.info(f"✅ طلب: {uid} - {cat} - {amt:,} ⭐")
                    return new_total, old_total
                    
        except Exception as e:
            logger.error(f"❌ خطأ add_order: {e}", exc_info=True)
            return None

order_manager = OrderManager()

# ============= دوال مساعدة =============
def get_rank(total: int) -> str:
    for threshold, title in RANKS:
        if total >= threshold:
            return title
    return RANKS[-1][1]

def validate_price(category: str, amount: int) -> bool:
    return category in PRICES and amount in PRICES[category]

# ============= 🛡️ معالجات البوت المحمية =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        user_id = user.id
        
        if not await rate_limiter.check_limit(user_id, 'command'):
            await update.message.reply_text(
                "⏳ الرجاء الانتظار قليلاً...\n"
                "لقد تجاوزت الحد المسموح من الطلبات."
            )
            return
        
        data = await order_manager.get_user_data(user_id)
        if not data:
            await update.message.reply_text("❌ حدث خطأ، حاول لاحقاً")
            return
        
        total = data['totalSpent']
        count = data['orderCount']
        rank = data['rank']
        
        # 🛡️ حماية 16: تنظيف اسم المستخدم
        safe_name = validator.sanitize_string(user.first_name, 50)
        
        keyboard = [[InlineKeyboardButton(
            "🛍️ افتح المتجر", 
            web_app=WebAppInfo(url=WEB_APP_URL)
        )]]
        
        await update.message.reply_text(
            f"🌟 متجر اللاشيء 🌟\n\n"
            f"مرحباً {safe_name}\n\n"
            f"🏷️ لقبك: {rank}\n"
            f"💰 إنفاقك: {total:,} ⭐\n"
            f"📦 طلباتك: {count}\n\n"
            f"اضغط الزر للدخول إلى المتجر",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        logger.info(f"👤 {user.id} - {safe_name} - استخدم /start")
        
    except Exception as e:
        logger.error(f"❌ خطأ start: {e}", exc_info=True)
        await update.message.reply_text("❌ حدث خطأ، حاول لاحقاً")

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🛡️ معالج WebApp محمي (حماية 11, 14)"""
    try:
        user = update.effective_user
        user_id = user.id
        
        if not await rate_limiter.check_limit(user_id, 'webapp'):
            await update.effective_message.reply_text(
                "⏳ الرجاء الانتظار...\n"
                "أنت ترسل طلبات كثيرة جداً."
            )
            return
        
        if not update.effective_message.web_app_data:
            logger.error(f"❌ [{user_id}] لا توجد web_app_data")
            return
        
        raw_data = update.effective_message.web_app_data.data
        
        # 🛡️ حماية 11: JSON Injection
        if len(raw_data) > 5000:
            logger.error(f"❌ [{user_id}] JSON كبير جداً: {len(raw_data)} bytes")
            await update.effective_message.reply_text("❌ بيانات كبيرة جداً")
            return
        
        logger.info(f"📥 [{user_id}] {validator.sanitize_string(user.first_name)}: {raw_data[:100]}")
        
        try:
            data = json.loads(raw_data)
            
            if isinstance(data, dict) and len(str(data)) > 1000:
                logger.error(f"❌ [{user_id}] JSON معقد جداً")
                await update.effective_message.reply_text("❌ بيانات معقدة")
                return
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ [{user_id}] JSON خاطئ: {e}")
            await update.effective_message.reply_text("❌ بيانات غير صالحة")
            return
        
        action = data.get('action')
        if action != 'buy':
            logger.warning(f"⚠️ [{user_id}] عملية غير معروفة: {action}")
            await update.effective_message.reply_text("❌ عملية غير معروفة")
            return
        
        category = validator.validate_category(data.get('category'))
        amount = validator.validate_amount(data.get('amount', 0))
        
        if not category or not amount:
            await update.effective_message.reply_text("❌ بيانات خاطئة")
            return
        
        if not validate_price(category, amount):
            logger.warning(f"⚠️ [{user_id}] سعر خاطئ: {category} - {amount}")
            await update.effective_message.reply_text(
                f"❌ سعر غير صحيح\n"
                f"الفئة: {category}\n"
                f"المبلغ: {amount:,} ⭐"
            )
            return
        
        if not await rate_limiter.check_limit(user_id, 'purchase'):
            await update.effective_message.reply_text(
                "⏳ لقد قمت بعمليات شراء كثيرة.\n"
                "الرجاء الانتظار قبل الشراء مرة أخرى."
            )
            return
        
        product = PRODUCTS[category]
        payload = f"order_{user_id}_{category}_{amount}_{int(datetime.now().timestamp())}"
        
        # 🛡️ حماية 14: Lock للمستخدم
        async with order_lock.get_lock(user_id):
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
        
        logger.info(f"📄 [{user_id}] فاتورة: {product['name']} - {amount:,} ⭐")
        
    except Exception as e:
        logger.error(f"❌ خطأ WebApp: {e}", exc_info=True)
        try:
            await update.effective_message.reply_text("❌ حدث خطأ، حاول لاحقاً")
        except:
            pass

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🛡️ فحص ما قبل الدفع (حماية 12)"""
    query = update.pre_checkout_query
    user_id = query.from_user.id
    
    try:
        parts = query.invoice_payload.split("_")
        if len(parts) != 5 or parts[0] != "order":
            logger.error(f"❌ [{user_id}] payload خاطئ: {query.invoice_payload}")
            await query.answer(ok=False, error_message="بيانات الطلب غير صحيحة")
            return
        
        payload_user_id = validator.validate_user_id(parts[1])
        if payload_user_id != user_id:
            logger.error(f"❌ [{user_id}] محاولة احتيال: payload user {payload_user_id}")
            await query.answer(ok=False, error_message="خطأ في التحقق")
            return
        
        category = validator.validate_category(parts[2])
        amount = validator.validate_amount(parts[3])
        
        if not category or not amount or not validate_price(category, amount):
            logger.error(f"❌ [{user_id}] بيانات خاطئة: {category} - {amount}")
            await query.answer(ok=False, error_message="بيانات غير صحيحة")
            return
        
        # 🛡️ حماية 12: Timestamp Manipulation
        timestamp = validator.validate_amount(parts[4])
        if timestamp:
            try:
                order_time = datetime.fromtimestamp(timestamp)
                if datetime.now() - order_time > timedelta(minutes=10):
                    logger.error(f"❌ [{user_id}] طلب قديم جداً: {order_time}")
                    await query.answer(ok=False, error_message="انتهت صلاحية الطلب")
                    return
            except (ValueError, OSError):
                pass
        
        await query.answer(ok=True)
        logger.info(f"✅ [{user_id}] تحقق ناجح")
        
    except Exception as e:
        logger.error(f"❌ خطأ precheckout: {e}", exc_info=True)
        await query.answer(ok=False, error_message="حدث خطأ")

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🛡️ معالج الدفع الناجح (حماية 20)"""
    user = update.effective_user
    payment = update.effective_message.successful_payment
    
    try:
        # 🛡️ حماية 20: فحص المبلغ والـ tip
        if payment.total_amount > 1_000_000:
            logger.warning(f"⚠️ [{user.id}] مبلغ ضخم: {payment.total_amount:,}")
        
        tip = getattr(payment, 'tip_amount', 0) or 0
        if tip > payment.total_amount:
            logger.error(f"❌ [{user.id}] tip مشبوه: {tip}")
            return
        
        parts = payment.invoice_payload.split("_")
        category = validator.validate_category(parts[2] if len(parts) > 2 else None)
        
        if not category:
            category = "unknown"
            logger.warning(f"⚠️ [{user.id}] فئة غير معروفة في الدفع")
        
        product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨"})
        
        result = await order_manager.add_order(user.id, payment.total_amount, category)
        
        if not result:
            logger.error(f"❌ [{user.id}] فشل حفظ الطلب")
            await update.effective_message.reply_text(
                "⚠️ تم الدفع لكن حدث خطأ في الحفظ.\n"
                "تواصل مع الدعم الفني."
            )
            if ADMIN_ID:
                try:
                    await context.bot.send_message(
                        ADMIN_ID,
                        f"🚨 خطأ حرج!\n\n"
                        f"المستخدم {user.id} دفع {payment.total_amount:,} ⭐\n"
                        f"لكن فشل حفظ الطلب في قاعدة البيانات!"
                    )
                except:
                    pass
            return
        
        new_total, old_total = result
        old_rank = get_rank(old_total)
        new_rank = get_rank(new_total)
        
        rank_up = ""
        if old_rank != new_rank:
            rank_up = f"\n\n🎊 ترقية!\n{old_rank} ➜ {new_rank}"
        
        await update.effective_message.reply_text(
            f"✅ تم الدفع بنجاح!\n\n"
            f"📦 {product['emoji']} {product['name']}\n"
            f"💰 {payment.total_amount:,} ⭐\n"
            f"🏷️ {new_rank}\n"
            f"💎 الإجمالي: {new_total:,} ⭐{rank_up}\n\n"
            f"شكراً لك ❤️"
        )
        
        logger.info(f"💳 [{user.id}] دفع ناجح: {payment.total_amount:,} ⭐")
        
        if ADMIN_ID:
            try:
                safe_name = validator.sanitize_string(user.first_name)
                safe_username = validator.sanitize_string(user.username or 'بدون username')
                await context.bot.send_message(
                    ADMIN_ID,
                    f"📢 طلب جديد\n\n"
                    f"👤 {safe_name} ({safe_username})\n"
                    f"🆔 {user.id}\n"
                    f"📦 {product['name']}\n"
                    f"💰 {payment.total_amount:,} ⭐\n"
                    f"🏷️ {new_rank}\n"
                    f"💎 إجمالي: {new_total:,} ⭐"
                )
            except Exception as e:
                logger.error(f"❌ فشل إرسال للأدمن: {e}")
                
    except Exception as e:
        logger.error(f"❌ خطأ successful_payment: {e}", exc_info=True)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء الشامل"""
    logger.error(f"❌ خطأ: {context.error}", exc_info=context.error)
    
    if ADMIN_ID and update:
        try:
            error_msg = str(context.error)[:200]
            user_info = ""
            
            if hasattr(update, 'effective_user') and update.effective_user:
                user_info = f"👤 {update.effective_user.id}"
            
            await context.bot.send_message(
                ADMIN_ID,
                f"🚨 خطأ في البوت\n\n"
                f"{user_info}\n"
                f"❌ {error_msg}"
            )
        except:
            pass

# ============= التهيئة =============
async def post_init(application):
    await order_manager.connect()
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت: @{bot.username}")
    logger.info(f"🌐 WebApp: {WEB_APP_URL}")
    logger.info(f"🛡️ نظام الحماية: 20 طبقة مفعلة")

async def pre_shutdown(application):
    if order_manager.pool:
        await order_manager.pool.close()
        logger.info("✅ إغلاق PostgreSQL")

# ============= التشغيل =============
def main():
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN خاطئ")
        sys.exit(1)
    
    # 🛡️ حماية 18: التحقق من WEBHOOK_SECRET
    if WEBHOOK_URL and (not WEBHOOK_SECRET or len(WEBHOOK_SECRET) < 10):
        logger.warning("⚠️ WEBHOOK_SECRET ضعيف أو مفقود!")
    
    logger.info("🚀 تشغيل البوت المحمي...")
    
    app = (Application.builder()
           .token(BOT_TOKEN)
           .post_init(post_init)
           .post_shutdown(pre_shutdown)
           .connection_pool_size(8)
           .build())
    
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
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
        logger.info("🌐 Webhook Mode (Protected)")
        logger.info(f"📍 {WEBHOOK_URL}")
        
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            drop_pending_updates=True,
            allowed_updates=["message", "pre_checkout_query"],
            secret_token=WEBHOOK_SECRET if WEBHOOK_SECRET and len(WEBHOOK_SECRET) >= 10 else None
        )
    else:
        logger.info("📡 Polling Mode (Protected)")
        
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
            
async def test_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختبار الفاتورة مباشرة"""
    user = update.message.from_user
    
    await update.message.reply_invoice(
        title="🔹 اختبار",
        description="اختبار الدفع بالنجوم",
        payload=f"test_{user.id}_{int(datetime.now().timestamp())}",
        provider_token="",
        currency="XTR",
        prices=[{'label': "السعر", 'amount': 5000}]
    )
    logger.info(f"📄 [{user.id}] فاتورة اختبار")

# في main() أضف:
app.add_handler(CommandHandler("invoice", test_invoice))






if __name__ == "__main__":
    main()

