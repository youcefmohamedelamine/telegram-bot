import os
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# الحصول على رابط قاعدة البيانات من متغيرات البيئة
DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    def __init__(self):
        self.database_url = DATABASE_URL
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """إنشاء اتصال بقاعدة البيانات"""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """إنشاء الجداول الأساسية"""
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
                    
                    # جدول الإحصائيات اليومية
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS daily_stats (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT REFERENCES users(user_id),
                            date DATE DEFAULT CURRENT_DATE,
                            taps INTEGER DEFAULT 0,
                            coins_earned INTEGER DEFAULT 0,
                            UNIQUE(user_id, date)
                        )
                    """)
                    
                    # جدول الدعوات
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS referrals (
                            id SERIAL PRIMARY KEY,
                            referrer_id BIGINT REFERENCES users(user_id),
                            referred_id BIGINT REFERENCES users(user_id),
                            reward_given BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(referred_id)
                        )
                    """)
                    
                    # جدول المهام
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_tasks (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT REFERENCES users(user_id),
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
        """إنشاء أو تحديث بيانات المستخدم"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # التحقق من وجود المستخدم
                    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        # تحديث المستخدم الموجود
                        cursor.execute("""
                            UPDATE users 
                            SET username = COALESCE(%s, username),
                                first_name = COALESCE(%s, first_name),
                                last_name = COALESCE(%s, last_name),
                                last_active = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                        """, (username, first_name, last_name, user_id))
                        logger.info(f"تم تحديث المستخدم: {user_id}")
                    else:
                        # إنشاء مستخدم جديد
                        cursor.execute("""
                            INSERT INTO users (user_id, username, first_name, last_name, invited_by)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (user_id, username, first_name, last_name, invited_by))
                        logger.info(f"تم إنشاء مستخدم جديد: {user_id}")
                        
                        # إضافة مكافأة الدعوة إذا كان هناك داعي
                        if invited_by:
                            self.add_referral(invited_by, user_id)
        except Exception as e:
            logger.error(f"خطأ في إنشاء/تحديث المستخدم: {e}")
    
    def get_user(self, user_id):
        """الحصول على بيانات المستخدم"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                    return dict(cursor.fetchone()) if cursor.rowcount > 0 else None
        except Exception as e:
            logger.error(f"خطأ في جلب بيانات المستخدم: {e}")
            return None
    
    def update_game_data(self, user_id, balance=None, taps_today=None, energy=None, level=None, tap_power=None):
        """تحديث بيانات اللعبة للمستخدم"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
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
        """إضافة دعوة جديدة"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # إضافة الدعوة
                    cursor.execute("""
                        INSERT INTO referrals (referrer_id, referred_id)
                        VALUES (%s, %s)
                        ON CONFLICT (referred_id) DO NOTHING
                    """, (referrer_id, referred_id))
                    
                    # تحديث عدد الدعوات وإضافة مكافأة
                    cursor.execute("""
                        UPDATE users 
                        SET invited_count = invited_count + 1,
                            balance = balance + 500
                        WHERE user_id = %s
                    """, (referrer_id,))
                    
                    logger.info(f"تمت إضافة دعوة: {referrer_id} -> {referred_id}")
        except Exception as e:
            logger.error(f"خطأ في إضافة الدعوة: {e}")
    
    def get_leaderboard(self, limit=10):
        """الحصول على قائمة المتصدرين"""
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
        """الحصول على جميع المستخدمين"""
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
        """عدد المستخدمين الكلي"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM users")
                    return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"خطأ في عد المستخدمين: {e}")
            return 0

# إنشاء نسخة واحدة من قاعدة البيانات
db = Database()
