import os
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/clicker_game")

class Database:
    def __init__(self):
        self.database_url = DATABASE_URL
        # إنشاء connection pool بدل فتح اتصال جديد في كل مرة
        self.connection_pool = pool.SimpleConnectionPool(
            1, 20,  # min, max connections
            self.database_url,
            connect_timeout=5
        )
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """الحصول على اتصال من pool"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"خطأ في الاتصال: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def init_database(self):
        """إنشاء الجداول والفهارس"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # جدول المستخدمين
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            user_id BIGINT PRIMARY KEY,
                            username VARCHAR(255),
                            first_name VARCHAR(255),
                            last_name VARCHAR(255),
                            balance BIGINT DEFAULT 0,
                            taps_today INTEGER DEFAULT 0,
                            energy INTEGER DEFAULT 1000,
                            level INTEGER DEFAULT 1,
                            tap_power INTEGER DEFAULT 1,
                            total_taps BIGINT DEFAULT 0,
                            invited_by BIGINT,
                            invited_count INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # إنشاء فهارس لتسريع الاستعلامات
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_users_balance 
                        ON users(balance DESC)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_users_created_at 
                        ON users(created_at DESC)
                    """)
                    
                    # جدول الإحصائيات اليومية
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS daily_stats (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                            date DATE DEFAULT CURRENT_DATE,
                            taps INTEGER DEFAULT 0,
                            coins_earned INTEGER DEFAULT 0,
                            UNIQUE(user_id, date)
                        )
                    """)
                    
                    # فهرس للبحث السريع عن الإحصائيات
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_daily_stats_user_date 
                        ON daily_stats(user_id, date)
                    """)
                    
                    # جدول الدعوات
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS referrals (
                            id SERIAL PRIMARY KEY,
                            referrer_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                            referred_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                            reward_given BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(referred_id)
                        )
                    """)
                    
                    # جدول المهام
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_tasks (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                            task_type VARCHAR(50),
                            completed BOOLEAN DEFAULT FALSE,
                            completed_at TIMESTAMP,
                            reward INTEGER DEFAULT 0,
                            UNIQUE(user_id, task_type)
                        )
                    """)
                    
                    logger.info("✅ تم إنشاء جداول قاعدة البيانات بنجاح")
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
    
    def create_or_update_user(self, user_id, username=None, first_name=None, last_name=None, invited_by=None):
        """إنشاء أو تحديث المستخدم - تحسين الأداء"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # استخدام INSERT ... ON CONFLICT بدل SELECT ثم UPDATE
                    cursor.execute("""
                        INSERT INTO users (user_id, username, first_name, last_name, invited_by)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            username = COALESCE(%s, users.username),
                            first_name = COALESCE(%s, users.first_name),
                            last_name = COALESCE(%s, users.last_name),
                            last_active = CURRENT_TIMESTAMP
                    """, (user_id, username, first_name, last_name, invited_by,
                          username, first_name, last_name))
                    
                    # إضافة الدعوة إذا لزم الأمر
                    if invited_by:
                        self.add_referral(invited_by, user_id)
                    
                    logger.info(f"تم حفظ/تحديث المستخدم: {user_id}")
        except Exception as e:
            logger.error(f"خطأ في إنشاء/تحديث المستخدم: {e}")
    
    def get_user(self, user_id):
        """جلب بيانات المستخدم - بدون معالجة غير ضرورية"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"خطأ في جلب بيانات المستخدم: {e}")
            return None
    
    def update_game_data(self, user_id, balance=None, taps_today=None, energy=None, level=None, tap_power=None):
        """تحديث بيانات اللعبة - استعلام واحد فقط"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # بناء الاستعلام بشكل ديناميكي فقط للحقول المطلوبة
                    updates = []
                    params = []
                    
                    if balance is not None:
                        updates.append("balance = %s")
                        params.append(balance)
                    if taps_today is not None:
                        updates.append("taps_today = %s")
                        params.append(taps_today)
                    if energy is not None:
                        updates.append("energy = %s")
                        params.append(energy)
                    if level is not None:
                        updates.append("level = %s")
                        params.append(level)
                    if tap_power is not None:
                        updates.append("tap_power = %s")
                        params.append(tap_power)
                    
                    if updates:
                        updates.append("last_active = CURRENT_TIMESTAMP")
                        params.append(user_id)
                        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
                        cursor.execute(query, params)
        except Exception as e:
            logger.error(f"خطأ في تحديث بيانات اللعبة: {e}")
    
    def add_referral(self, referrer_id, referred_id):
        """إضافة دعوة"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # فحص وإضافة وتحديث في عملية واحدة
                    cursor.execute("""
                        INSERT INTO referrals (referrer_id, referred_id)
                        VALUES (%s, %s)
                        ON CONFLICT (referred_id) DO NOTHING
                    """, (referrer_id, referred_id))
                    
                    # تحديث الرصيد والعدد
                    cursor.execute("""
                        UPDATE users 
                        SET invited_count = invited_count + 1,
                            balance = balance + 500
                        WHERE user_id = %s AND invited_count < 999
                    """, (referrer_id,))
                    
                    logger.info(f"تمت إضافة دعوة: {referrer_id} -> {referred_id}")
        except Exception as e:
            logger.error(f"خطأ في إضافة الدعوة: {e}")
    
    def get_leaderboard(self, limit=10):
        """جلب المتصدرين - استعلام محسّن"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT user_id, username, first_name, balance, level, total_taps
                        FROM users
                        ORDER BY balance DESC
                        LIMIT %s
                    """, (limit,))
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في جلب المتصدرين: {e}")
            return []
    
    def get_all_users(self):
        """جلب جميع المستخدمين"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT user_id, username, first_name, balance, level, 
                               created_at, last_active
                        FROM users
                        ORDER BY created_at DESC
                    """)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في جلب المستخدمين: {e}")
            return []
    
    def get_user_count(self):
        """عد المستخدمين"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM users")
                    return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"خطأ في عد المستخدمين: {e}")
            return 0
    
    def close(self):
        """إغلاق جميع الاتصالات"""
        if self.connection_pool:
            self.connection_pool.closeall()

# إنشاء نسخة واحدة من قاعدة البيانات
db = Database()
