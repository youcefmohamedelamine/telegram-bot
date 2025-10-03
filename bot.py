import sqlite3
import time
import os
from datetime import datetime, timedelta
from functools import wraps

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ====== إعدادات - غيّرها ======
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_هنا_توكن_البوت")
OWNER_ID = int(os.environ.get("OWNER_ID", "123456789"))   # رقمك في التليجرام
PRICE_STARS = int(os.environ.get("PRICE_STARS", "100"))      # عدد النجوم المطلوبة
LIKES_AMOUNT = int(os.environ.get("LIKES_AMOUNT", "100"))    # عدد اللايكات
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", str(24 * 3600)))  # كل 24 ساعة
DB_PATH = os.environ.get("DB_PATH", "bot_db.sqlite3")
# ==============================

# ---------- قاعدة البيانات ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        stars INTEGER DEFAULT 0,
        last_purchase INTEGER DEFAULT 0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pending_orders (
        user_id INTEGER,
        amount INTEGER,
        created_at INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, stars, last_purchase FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"user_id": row[0], "username": row[1], "stars": row[2], "last_purchase": row[3]}
    return None

def ensure_user(user_id, username=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users(user_id, username, stars, last_purchase) VALUES (?, ?, 0, 0)",
                (user_id, username))
    cur.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    conn.commit()
    conn.close()

def update_stars(user_id, new_stars):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET stars = ? WHERE user_id = ?", (new_stars, user_id))
    conn.commit()
    conn.close()

def set_last_purchase(user_id, ts):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_purchase = ? WHERE user_id = ?", (ts, user_id))
    conn.commit()
    conn.close()

# ---------- أدوات ----------
def secs_to_human(secs):
    td = timedelta(seconds=secs)
    h = td.seconds // 3600
    m = (td.seconds % 3600) // 60
    return f"{h}h {m}m"

def owner_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user and update.effective_user.id == OWNER_ID:
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text("❌ هذا الأمر مخصص لصاحب البوت فقط.")
    return wrapped

# ---------- أوامر ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username)
    await update.message.reply_text(
        f"مرحباً {user.first_name} 👋\n\n"
        f"يمكنك شراء {LIKES_AMOUNT} لايك مقابل {PRICE_STARS} نجمة.\n"
        f"للبدء استخدم الأمر /buy\n"
        f"رصيدك الحالي: /balance"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 الأوامر المتاحة:\n"
        "/buy - شراء لايكات\n"
        "/balance - عرض رصيد النجوم\n"
        "/help - عرض هذه القائمة\n\n"
        "💡 بعد الشراء سيُطلب منك كتابة ID لعبة Free Fire الخاص بك."
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username)
    u = get_user(user.id)
    next_allowed = 0
    if u and u["last_purchase"]:
        next_allowed = u["last_purchase"] + COOLDOWN_SECONDS
    now_ts = int(time.time())
    if next_allowed > now_ts:
        remaining = next_allowed - now_ts
        await update.message.reply_text(f"رصيدك: {u['stars']} ⭐\n⏳ الشراء متاح بعد: {secs_to_human(remaining)}")
    else:
        await update.message.reply_text(f"رصيدك: {u['stars']} ⭐\n✅ يمكنك الشراء الآن.")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username)
    u = get_user(user.id)
    now_ts = int(time.time())

    # تحقق من الكولداون
    if u["last_purchase"] and (now_ts - u["last_purchase"] < COOLDOWN_SECONDS):
        remaining = COOLDOWN_SECONDS - (now_ts - u["last_purchase"])
        await update.message.reply_text(f"❌ يمكنك الشراء مرة كل 24 ساعة.\nتبقى: {secs_to_human(remaining)}")
        return

    # تحقق من الرصيد
    if u["stars"] < PRICE_STARS:
        await update.message.reply_text(f"رصيدك غير كافٍ. تحتاج {PRICE_STARS} نجمة ولكن لديك {u['stars']} ⭐")
        return

    # خصم النجوم وإنشاء طلب معلق
    new_balance = u["stars"] - PRICE_STARS
    update_stars(user.id, new_balance)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO pending_orders(user_id, amount, created_at) VALUES (?, ?, ?)",
                (user.id, LIKES_AMOUNT, now_ts))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ تم خصم {PRICE_STARS} نجمة من رصيدك.\n"
        f"💬 أرسل الآن ID لعبة Free Fire الخاص بك لكي أرسله لصاحب البوت."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT amount FROM pending_orders WHERE user_id = ?", (user.id,))
    row = cur.fetchone()
    if row:
        amount = row[0]
        # حذف الطلب من قائمة المعلقين
        cur.execute("DELETE FROM pending_orders WHERE user_id = ?", (user.id,))
        conn.commit()
        conn.close()

        set_last_purchase(user.id, int(time.time()))
        await update.message.reply_text(f"🎉 تم استلام ID الخاص بك ({text}).\nسيقوم صاحب البوت بإضافة {amount} لايك قريباً.")

        # إرسال إشعار لصاحب البوت
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"💰 عملية شراء جديدة:\n\n"
                f"👤 المستخدم: @{user.username or user.id}\n"
                f"🆔 تيليجرام: {user.id}\n"
                f"🎮 Free Fire ID: {text}\n"
                f"👍 لايكات: {amount}\n"
                f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        )
    else:
        conn.close()
        await update.message.reply_text("📌 رسالتك تم استلامها. إذا أردت شراء لايكات استخدم /buy.")

# ----- أمر إداري لإضافة نجوم -----
@owner_only
async def add_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("استخدام: /addstars <user_id> <amount>")
        return
    try:
        target_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ القيم يجب أن تكون أرقام.")
        return

    ensure_user(target_id, None)
    u = get_user(target_id)
    new_balance = u["stars"] + amount
    update_stars(target_id, new_balance)
    await update.message.reply_text(f"تمت إضافة {amount} ⭐ للمستخدم {target_id}. الرصيد الجديد: {new_balance} ⭐")

# ---------- تشغيل البوت ----------
def main():
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("addstars", add_stars))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
