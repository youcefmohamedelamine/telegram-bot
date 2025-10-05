import os
import asyncpg # المكتبة البديلة لـ sqlite3 للعمل مع PostgreSQL

# لا حاجة لاستخدام DATABASE من config، نعتمد على متغير البيئة
DATABASE_URL = os.getenv("DATABASE_URL")
pool = None # لتخزين مجمع الاتصال (Connection Pool)

async def setup_db():
    """تهيئة مجمع الاتصال وإنشاء الجداول."""
    global pool
    if not DATABASE_URL:
        # إذا لم يكن DATABASE_URL موجوداً، هذا يعني أن خدمة PostgreSQL غير مضافة أو غير معرّفة
        print("❌ خطأ: متغير البيئة DATABASE_URL غير موجود. تأكد من إضافة خدمة PostgreSQL على Railway.")
        return

    # إنشاء مجمع الاتصال (Connection Pool)
    pool = await asyncpg.create_pool(DATABASE_URL)
    
    # استخدام اتصال واحد لإنشاء الجداول
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                user_id BIGINT, 
                payment_id TEXT PRIMARY KEY,
                amount INTEGER NOT NULL,
                currency TEXT NOT NULL,
                # يمكنك إضافة حقول أخرى هنا مثل 'payload' أو 'timestamp'
                payment_timestamp TIMESTAMP DEFAULT NOW()
            );
        ''')
        # تم حذف PRIMARY KEY (user_id, payment_id) واكتفيت بـ payment_id PRIMARY KEY
        # لجعل الكود أكثر وضوحاً
        print("✅ تم إعداد جداول PostgreSQL بنجاح.")

async def save_payment(user_id, payment_id, amount, currency):
    """حفظ سجل الدفع في قاعدة بيانات PostgreSQL."""
    if not pool:
        print("❌ خطأ: لم يتم تهيئة مجمع الاتصال بعد.")
        return

    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO payments (user_id, payment_id, amount, currency)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (payment_id) DO NOTHING; -- تجنب إدخال الدفعة نفسها مرتين
        ''', user_id, payment_id, amount, currency)

async def get_payment_details(payment_id):
    """استرجاع تفاصيل الدفع بناءً على payment_id."""
    if not pool:
        print("❌ خطأ: لم يتم تهيئة مجمع الاتصال بعد.")
        return

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT user_id, amount, currency FROM payments WHERE payment_id = $1', 
            payment_id
        )
        # يعيد قاموس (Record) أو None
        return row
