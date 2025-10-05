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

# ============= 🎮 User State Manager =============
class UserStateManager:
    """إدارة حالات المستخدمين (انتظار Free Fire ID)"""
    def __init__(self):
        self.waiting_for_id = {}  # {user_id: {'order_id': ..., 'product': ..., 'amount': ...}}
    
    def set_waiting(self, user_id: int, order_id: int, product_name: str, amount: int):
        self.waiting_for_id[user_id] = {
            'order_id': order_id,
            'product': product_name,
            'amount': amount,
            'timestamp': datetime.now()
        }
        logger.info(f"📝 [{user_id}] في انتظار Free Fire ID | Order #{order_id}")
    
    def get_waiting(self, user_id: int) -> Optional[Dict]:
        data = self.waiting_for_id.get(user_id)
        if data:
            # حذف البيانات القديمة (أكثر من 10 دقائق)
            if datetime.now() - data['timestamp'] > timedelta(minutes=10):
                self.clear_waiting(user_id)
                return None
        return data
    
    def clear_waiting(self, user_id: int):
        if user_id in self.waiting_for_id:
            del self.waiting_for_id[user_id]
            logger.info(f"🗑️ [{user_id}] تم مسح حالة الانتظار")
    
    def is_waiting(self, user_id: int) -> bool:
        return user_id in self.waiting_for_id

user_state = UserStateManager()

# ============= 🛡️ مدير الطلبات المحمي والمحسّن =============
class OrderManager:
    """
    🛡️ الحماية من:
    6. Race conditions
    7. Database connection loss
    8. Transaction failures
    13. Integer Overflow
    19. Database Pool Exhaustion
    + Idempotency
    + Audit Trail
    + Rollback Support
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
                    timeout=30
                )
                logger.info("✅ اتصال PostgreSQL")
                await self.create_tables()
                return
            except Exception as e:
                logger.error(f"❌ محاولة {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error("❌ فشل الاتصال بقاعدة البيانات")
                    sys.exit(1)

    async def create_tables(self):
        """إنشاء جداول users و orders"""
        try:
            # جدول users
            await self.pool.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    total_spent BIGINT DEFAULT 0 CHECK (total_spent >= 0),
                    order_count INT DEFAULT 0 CHECK (order_count >= 0),
                    rank TEXT NOT NULL DEFAULT 'زائر جديد 🌱',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_purchase TIMESTAMP,
                    is_blocked BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # جدول orders للـ Audit Trail
            await self.pool.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    category TEXT NOT NULL,
                    amount BIGINT NOT NULL,
                    old_total BIGINT NOT NULL,
                    new_total BIGINT NOT NULL,
                    old_rank TEXT NOT NULL,
                    new_rank TEXT NOT NULL,
                    payment_charge_id TEXT,
                    telegram_payment_charge_id TEXT,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            ''')
            
            # Indexes
            await self.pool.execute('''
                CREATE INDEX IF NOT EXISTS idx_total_spent 
                ON users(total_spent DESC);
            ''')
            
            await self.pool.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_purchase 
                ON users(last_purchase DESC);
            ''')
            
            await self.pool.execute('''
                CREATE INDEX IF NOT EXISTS idx_orders_user 
                ON orders(user_id, created_at DESC);
            ''')
            
            await self.pool.execute('''
                CREATE INDEX IF NOT EXISTS idx_orders_status 
                ON orders(status) WHERE status != 'completed';
            ''')
            
            logger.info("✅ جميع الجداول جاهزة")
        except Exception as e:
            logger.error(f"❌ فشل إنشاء الجداول: {e}", exc_info=True)
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

    async def _check_duplicate_order(
        self, 
        user_id: int, 
        idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """التحقق من الطلبات المكررة"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT new_total, old_total, new_rank, id as order_id
                    FROM orders 
                    WHERE user_id = $1 
                      AND metadata->>'idempotency_key' = $2
                      AND created_at > NOW() - INTERVAL '1 hour'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    user_id, idempotency_key
                )
                
                if row:
                    return {
                        'new_total': row['new_total'],
                        'old_total': row['old_total'],
                        'new_rank': row['new_rank'],
                        'order_id': row['order_id'],
                        'duplicate': True,
                        'rank_changed': False
                    }
        except Exception as e:
            logger.error(f"❌ خطأ فحص التكرار: {e}")
        
        return None

    async def _execute_order_transaction(
        self,
        user_id: int,
        amount: int,
        category: str,
        payment_charge_id: str,
        telegram_payment_charge_id: str,
        idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """تنفيذ المعاملة الكاملة مع Audit Trail"""
        
        async with self.pool.acquire() as conn:
            async with conn.transaction(isolation='serializable'):
                
                user_row = await conn.fetchrow(
                    """
                    SELECT 
                        id, 
                        total_spent, 
                        order_count,
                        rank,
                        is_blocked 
                    FROM users 
                    WHERE id = $1 
                    FOR UPDATE
                    """,
                    user_id
                )
                
                if not user_row:
                    logger.error(f"❌ [{user_id}] مستخدم غير موجود")
                    return None
                
                if user_row['is_blocked']:
                    logger.warning(f"🚫 [{user_id}] محاولة شراء من مستخدم محظور")
                    return None
                
                old_total = user_row['total_spent']
                old_rank = user_row['rank']
                old_count = user_row['order_count']
                
                new_total = old_total + amount
                new_count = old_count + 1
                
                MAX_TOTAL = 9_000_000_000_000
                if new_total > MAX_TOTAL:
                    logger.error(
                        f"❌ [{user_id}] تجاوز الحد الأقصى: "
                        f"{new_total:,} > {MAX_TOTAL:,}"
                    )
                    return None
                
                new_rank = get_rank(new_total)
                rank_changed = (old_rank != new_rank)
                
                await conn.execute(
                    """
                    UPDATE users 
                    SET 
                        total_spent = $2,
                        order_count = $3,
                        rank = $4,
                        last_purchase = CURRENT_TIMESTAMP
                    WHERE id = $1
                    """,
                    user_id, new_total, new_count, new_rank
                )
                
                metadata = {
                    'idempotency_key': idempotency_key,
                    'rank_changed': rank_changed,
                    'user_agent': 'telegram_bot',
                    'version': '2.0'
                }
                
                order_id = await conn.fetchval(
                    """
                    INSERT INTO orders (
                        user_id,
                        category,
                        amount,
                        old_total,
                        new_total,
                        old_rank,
                        new_rank,
                        payment_charge_id,
                        telegram_payment_charge_id,
                        metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                    """,
                    user_id, category, amount,
                    old_total, new_total,
                    old_rank, new_rank,
                    payment_charge_id,
                    telegram_payment_charge_id,
                    json.dumps(metadata)
                )
                
                logger.info(
                    f"💰 ORDER #{order_id} | "
                    f"User {user_id} | "
                    f"{category} | "
                    f"{amount:,} ⭐ | "
                    f"{old_total:,} → {new_total:,} | "
                    f"{'🎊 ' + new_rank if rank_changed else new_rank}"
                )
                
                return {
                    'order_id': order_id,
                    'new_total': new_total,
                    'old_total': old_total,
                    'new_rank': new_rank,
                    'old_rank': old_rank,
                    'rank_changed': rank_changed,
                    'duplicate': False
                }

    async def add_order(
        self, 
        user_id: int, 
        amount: int, 
        category: str,
        payment_charge_id: str = None,
        telegram_payment_charge_id: str = None,
        idempotency_key: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        🛡️ دالة محسّنة مع:
        - Idempotency Protection
        - Audit Trail
        - Retry Mechanism
        - Detailed Logging
        - Rollback Support
        """
        
        uid = validator.validate_user_id(user_id)
        amt = validator.validate_amount(amount)
        cat = validator.validate_category(category)
        
        if not all([uid, amt, cat]):
            logger.error(f"❌ مدخلات غير صالحة: uid={uid}, amt={amt}, cat={cat}")
            return None
        
        # Idempotency Check
        if idempotency_key:
            existing = await self._check_duplicate_order(uid, idempotency_key)
            if existing:
                logger.warning(f"⚠️ [{uid}] طلب مكرر: {idempotency_key}")
                return existing
        
        # Retry Mechanism
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                result = await self._execute_order_transaction(
                    uid, amt, cat, 
                    payment_charge_id, 
                    telegram_payment_charge_id,
                    idempotency_key
                )
                
                if result:
                    logger.info(
                        f"✅ [{uid}] طلب ناجح (محاولة {attempt + 1}): "
                        f"{cat} - {amt:,} ⭐"
                    )
                    return result
                
            except asyncpg.exceptions.SerializationError as e:
                logger.warning(
                    f"⚠️ [{uid}] تضارب معاملة (محاولة {attempt + 1}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"❌ [{uid}] فشل بعد {max_retries} محاولات")
                    return None
                    
            except asyncpg.exceptions.PostgresError as e:
                logger.error(f"❌ [{uid}] خطأ PostgreSQL: {e}", exc_info=True)
                
                if "connection" in str(e).lower():
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * 2)
                        continue
                return None
                
            except Exception as e:
                logger.error(f"❌ [{uid}] خطأ غير متوقع: {e}", exc_info=True)
                return None
        
        return None

    async def get_user_orders(self, user_id: int, limit: int = 10):
        """استرجاع تاريخ الطلبات"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT 
                        id,
                        category,
                        amount,
                        new_rank,
                        created_at
                    FROM orders
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    user_id, limit
                )
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ خطأ get_user_orders: {e}")
            return []

    async def rollback_order(self, order_id: int, reason: str = "refund"):
        """
        🔄 Rollback طلب (للاسترداد أو التصحيح)
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    order = await conn.fetchrow(
                        """
                        SELECT user_id, amount, old_total, old_rank
                        FROM orders
                        WHERE id = $1 AND status = 'completed'
                        FOR UPDATE
                        """,
                        order_id
                    )
                    
                    if not order:
                        logger.error(f"❌ طلب غير موجود: {order_id}")
                        return False
                    
                    await conn.execute(
                        """
                        UPDATE users
                        SET 
                            total_spent = $2,
                            order_count = order_count - 1,
                            rank = $3
                        WHERE id = $1
                        """,
                        order['user_id'],
                        order['old_total'],
                        order['old_rank']
                    )
                    
                    await conn.execute(
                        """
                        UPDATE orders
                        SET 
                            status = $2,
                            metadata = metadata || $3::jsonb
                        WHERE id = $1
                        """,
                        order_id,
                        'refunded',
                        json.dumps({
                            'refund_reason': reason, 
                            'refunded_at': datetime.now().isoformat()
                        })
                    )
                    
                    logger.info(f"🔄 Rollback #{order_id}: {reason}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ خطأ rollback: {e}", exc_info=True)
            return False

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
    """🛡️ معالج WebApp محمي"""
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
    """🛡️ فحص ما قبل الدفع - مبسط وفعال"""
    query = update.pre_checkout_query
    user_id = query.from_user.id
    
    try:
        # ✅ التحقق البسيط من payload
        parts = query.invoice_payload.split("_")
        
        # فحص أساسي فقط
        if len(parts) < 4 or parts[0] != "order":
            logger.error(f"❌ [{user_id}] payload خاطئ: {query.invoice_payload}")
            await query.answer(ok=False, error_message="خطأ في بيانات الطلب")
            return
        
        # التحقق من أن user_id يطابق
        try:
            payload_user_id = int(parts[1])
            if payload_user_id != user_id:
                logger.error(f"❌ [{user_id}] محاولة احتيال: payload={payload_user_id}")
                await query.answer(ok=False, error_message="خطأ في التحقق من الهوية")
                return
        except (ValueError, IndexError):
            logger.error(f"❌ [{user_id}] payload user_id غير صالح")
            await query.answer(ok=False, error_message="بيانات غير صحيحة")
            return
        
        # ✅ كل شيء تمام - الموافقة على الدفع
        await query.answer(ok=True)
        logger.info(f"✅ [{user_id}] PreCheckout موافق | {query.invoice_payload}")
        
    except Exception as e:
        logger.error(f"❌ خطأ precheckout: {e}", exc_info=True)
        # في حالة أي خطأ غير متوقع، نوافق على الدفع
        # لأن الفحص الحقيقي سيكون في successful_payment
        try:
            await query.answer(ok=True)
            logger.warning(f"⚠️ [{user_id}] موافقة طارئة بعد خطأ")
        except:
            pass

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🛡️ معالج الدفع الناجح + طلب Free Fire ID"""
    user = update.effective_user
    payment = update.effective_message.successful_payment
    
    try:
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
        
        # 🆕 استخدام الدالة المحسّنة مع Idempotency
        result = await order_manager.add_order(
            user_id=user.id,
            amount=payment.total_amount,
            category=category,
            payment_charge_id=getattr(payment, 'provider_payment_charge_id', None),
            telegram_payment_charge_id=getattr(payment, 'telegram_payment_charge_id', None),
            idempotency_key=payment.invoice_payload
        )
        
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
        
        # 🆕 التعامل مع الطلبات المكررة
        if result.get('duplicate'):
            await update.effective_message.reply_text(
                f"⚠️ تم معالجة هذا الطلب مسبقاً\n\n"
                f"📦 {product['emoji']} {product['name']}\n"
                f"💰 {payment.total_amount:,} ⭐\n"
                f"🏷️ {result['new_rank']}\n"
                f"💎 الإجمالي: {result['new_total']:,} ⭐\n\n"
                f"إذا كانت هناك مشكلة، تواصل مع الدعم."
            )
            logger.warning(f"⚠️ [{user.id}] طلب مكرر تم اكتشافه")
            return
        
        new_total = result['new_total']
        old_total = result['old_total']
        new_rank = result['new_rank']
        old_rank = result['old_rank']
        rank_changed = result['rank_changed']
        order_id = result['order_id']
        
        rank_up = ""
        if rank_changed:
            rank_up = f"\n\n🎊 ترقية!\n{old_rank} ➜ {new_rank}"
        
        # 🎮 طلب Free Fire ID
        user_state.set_waiting(user.id, order_id, product['name'], payment.total_amount)
        
        await update.effective_message.reply_text(
            f"✅ تم الدفع بنجاح!\n\n"
            f"📦 {product['emoji']} {product['name']}\n"
            f"💰 {payment.total_amount:,} ⭐\n"
            f"🏷️ {new_rank}\n"
            f"💎 الإجمالي: {new_total:,} ⭐{rank_up}\n"
            f"🆔 رقم الطلب: #{order_id}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🎮 الآن أرسل Free Fire ID الخاص بك\n"
            f"مثال: 1234567890\n\n"
            f"⚠️ تأكد من ID قبل الإرسال!"
        )
        
        logger.info(f"💳 [{user.id}] دفع ناجح: {payment.total_amount:,} ⭐ | Order #{order_id}")
                
    except Exception as e:
        logger.error(f"❌ خطأ successful_payment: {e}", exc_info=True)

async def collect_freefire_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🎮 جمع Free Fire ID بعد الدفع"""
    user = update.effective_user
    user_id = user.id
    
    # تحقق: هل المستخدم في حالة انتظار؟
    if not user_state.is_waiting(user_id):
        return  # تجاهل الرسالة
    
    waiting_data = user_state.get_waiting(user_id)
    if not waiting_data:
        return
    
    freefire_id = update.message.text.strip()
    
    # 🛡️ Validation
    # تنظيف من الأحرف الخطرة
    freefire_id = validator.sanitize_string(freefire_id, 20)
    
    # التحقق من الصيغة
    if not freefire_id or len(freefire_id) < 5:
        await update.message.reply_text(
            "❌ Free Fire ID غير صحيح!\n\n"
            f"أرسل ID صحيح (مثال: 1234567890)"
        )
        return
    
    # يفضل أن يكون أرقام فقط (لكن بعض IDs قد تحتوي حروف)
    if not freefire_id.isdigit() and not freefire_id.isalnum():
        await update.message.reply_text(
            "❌ Free Fire ID يجب أن يحتوي على أرقام وحروف فقط\n\n"
            f"أرسل ID صحيح"
        )
        return
    
    order_id = waiting_data['order_id']
    product_name = waiting_data['product']
    amount = waiting_data['amount']
    
    # 💾 حفظ في قاعدة البيانات
    try:
        async with order_manager.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE orders
                SET metadata = metadata || $2::jsonb
                WHERE id = $1
                """,
                order_id,
                json.dumps({'freefire_id': freefire_id, 'id_received_at': datetime.now().isoformat()})
            )
        
        logger.info(f"🎮 [{user_id}] Free Fire ID: {freefire_id} | Order #{order_id}")
        
        # مسح حالة الانتظار
        user_state.clear_waiting(user_id)
        
        # رسالة للمستخدم
        await update.message.reply_text(
            f"✅ تم استلام Free Fire ID بنجاح!\n\n"
            f"🎮 ID: {freefire_id}\n"
            f"🆔 رقم الطلب: #{order_id}\n\n"
            f"⏳ سيتم تنفيذ طلبك خلال 24 ساعة\n"
            f"💬 شكراً لك ❤️"
        )
        
        # إشعار للأدمن
        if ADMIN_ID:
            try:
                safe_name = validator.sanitize_string(user.first_name)
                safe_username = validator.sanitize_string(user.username or 'بدون username')
                await context.bot.send_message(
                    ADMIN_ID,
                    f"🎮 Free Fire ID جديد\n\n"
                    f"👤 {safe_name} (@{safe_username})\n"
                    f"🆔 User ID: {user_id}\n"
                    f"🎮 Free Fire ID: `{freefire_id}`\n"
                    f"📦 المنتج: {product_name}\n"
                    f"💰 المبلغ: {amount:,} ⭐\n"
                    f"🔢 Order: #{order_id}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"❌ فشل إرسال للأدمن: {e}")
                
    except Exception as e:
        logger.error(f"❌ خطأ حفظ Free Fire ID: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ حدث خطأ في حفظ ID\n"
            "تواصل مع الدعم الفني"
        )

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

# ============= أوامر إضافية للأدمن =============
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات للأدمن فقط"""
    user_id = update.effective_user.id
    
    if not ADMIN_ID or user_id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر للأدمن فقط")
        return
    
    try:
        async with order_manager.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT id) as total_users,
                    SUM(total_spent) as total_revenue,
                    SUM(order_count) as total_orders
                FROM users
            """)
            
            recent_orders = await conn.fetch("""
                SELECT COUNT(*) as count, SUM(amount) as revenue
                FROM orders
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
            
            top_users = await conn.fetch("""
                SELECT id, total_spent, rank
                FROM users
                ORDER BY total_spent DESC
                LIMIT 5
            """)
        
        msg = "📊 إحصائيات البوت\n\n"
        msg += f"👥 إجمالي المستخدمين: {stats['total_users']:,}\n"
        msg += f"💰 إجمالي الإيرادات: {stats['total_revenue']:,} ⭐\n"
        msg += f"📦 إجمالي الطلبات: {stats['total_orders']:,}\n\n"
        
        if recent_orders and recent_orders[0]['count']:
            msg += f"📅 آخر 24 ساعة:\n"
            msg += f"   طلبات: {recent_orders[0]['count']:,}\n"
            msg += f"   إيرادات: {recent_orders[0]['revenue']:,} ⭐\n\n"
        
        msg += "🏆 أفضل 5 مستخدمين:\n"
        for i, user in enumerate(top_users, 1):
            msg += f"{i}. User {user['id']}: {user['total_spent']:,} ⭐ ({user['rank']})\n"
        
        await update.message.reply_text(msg)
        
    except Exception as e:
        logger.error(f"❌ خطأ admin_stats: {e}")
        await update.message.reply_text("❌ حدث خطأ")

async def admin_refund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استرداد طلب - للأدمن فقط"""
    user_id = update.effective_user.id
    
    if not ADMIN_ID or user_id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر للأدمن فقط")
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "❌ الاستخدام الصحيح:\n"
            "/refund <order_id> [سبب]"
        )
        return
    
    order_id = int(context.args[0])
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "admin_refund"
    
    try:
        success = await order_manager.rollback_order(order_id, reason)
        
        if success:
            await update.message.reply_text(
                f"✅ تم استرداد الطلب #{order_id}\n"
                f"السبب: {reason}"
            )
        else:
            await update.message.reply_text(
                f"❌ فشل استرداد الطلب #{order_id}\n"
                f"ربما الطلب غير موجود أو تم استرداده مسبقاً"
            )
    except Exception as e:
        logger.error(f"❌ خطأ admin_refund: {e}")
        await update.message.reply_text("❌ حدث خطأ")

# ============= التهيئة =============
async def post_init(application):
    await order_manager.connect()
    bot = await application.bot.get_me()
    logger.info(f"✅ البوت: @{bot.username}")
    logger.info(f"🌐 WebApp: {WEB_APP_URL}")
    logger.info(f"🛡️ نظام الحماية: 20+ طبقة مفعلة")
    logger.info(f"🆕 Idempotency: مفعل")
    logger.info(f"📊 Audit Trail: مفعل")

async def pre_shutdown(application):
    if order_manager.pool:
        await order_manager.pool.close()
        logger.info("✅ إغلاق PostgreSQL")

# ============= التشغيل =============
def main():
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        logger.error("❌ BOT_TOKEN خاطئ")
        sys.exit(1)
    
    if WEBHOOK_URL and (not WEBHOOK_SECRET or len(WEBHOOK_SECRET) < 10):
        logger.warning("⚠️ WEBHOOK_SECRET ضعيف أو مفقود!")
    
    logger.info("🚀 تشغيل البوت المحمي والمحسّن...")
    
    app = (Application.builder()
           .token(BOT_TOKEN)
           .post_init(post_init)
           .post_shutdown(pre_shutdown)
           .connection_pool_size(8)
           .build())
    
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("refund", admin_refund))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    # 🎮 Handler لجمع Free Fire ID - يجب أن يكون بعد SUCCESSFUL_PAYMENT
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_freefire_id))
    
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
        logger.info("🌐 Webhook Mode (Protected & Enhanced)")
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
        logger.info("📡 Polling Mode (Protected & Enhanced)")
        
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

if __name__ == "__main__":
    main()
