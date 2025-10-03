
import sqlite3
import time
from datetime import datetime, timedelta
from functools import wraps

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# ====== إعدادات - غيّرها ======
TELEGRAM_TOKEN = "ضع_هنا_توكن_البوت"
OWNER_ID = 123456789   # رقمك في التليجرام كصاحب البوت
PRICE_STARS = 100      # عدد النجوم المطلوبة
LIKES_AMOUNT = 100     # عدد اللايكات
COOLDOWN_SECONDS = 24 * 3600  # كل 24 ساعة
DB_PATH = "bot_db.sqlite3"
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
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        if update.effective_user and update.effective_user.id == OWNER_ID:
            return func(update, context, *args, **kwargs)
        else:
            update.message.reply_text("❌ هذا الأمر مخصص لصاحب البوت فقط.")
    return wrapped

# ---------- أوامر ----------
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    ensure_user(user.id, user.username)
    update.message.reply_text(
        f"مرحباً {user.first_name} 👋\n\n"
        f"يمكنك شراء {LIKES_AMOUNT} لايك مقابل {PRICE_STARS} نجمة.\n"
        f"للبدء استخدم الأمر /buy\n"
        f"رصيدك الحالي: /balance"
    )

def help_cmd(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📌 الأوامر المتاحة:\n"
        "/buy - شراء لايكات\n"
        "/balance - عرض رصيد النجوم\n"
        "/help - عرض هذه القائمة\n\n"
        "💡 بعد الشراء سيُطلب منك كتابة ID لعبة Free Fire الخاص بك."
    )

def balance(update: Update, context: CallbackContext):
    user = update.effective_user
    ensure_user(user.id, user.username)
    u = get_user(user.id)
    next_allowed = 0
    if u and u["last_purchase"]:
        next_allowed = u["last_purchase"] + COOLDOWN_SECONDS
    now_ts = int(time.time())
    if next_allowed > now_ts:
        remaining = next_allowed - now_ts
        update.message.reply_text(f"رصيدك: {u['stars']} ⭐\n⏳ الشراء متاح بعد: {secs_to_human(remaining)}")
    else:
        update.message.reply_text(f"رصيدك: {u['stars']} ⭐\n✅ يمكنك الشراء الآن.")

def buy(update: Update, context: CallbackContext):
    user = update.effective_user
    ensure_user(user.id, user.username)
    u = get_user(user.id)
    now_ts = int(time.time())

    # تحقق من الكولداون
    if u["last_purchase"] and (now_ts - u["last_purchase"] < COOLDOWN_SECONDS):
        remaining = COOLDOWN_SECONDS - (now_ts - u["last_purchase"])
        update.message.reply_text(f"❌ يمكنك الشراء مرة كل 24 ساعة.\nتبقى: {secs_to_human(remaining)}")
        return

    # تحقق من الرصيد
    if u["stars"] < PRICE_STARS:
        update.message.reply_text(f"رصيدك غير كافٍ. تحتاج {PRICE_STARS} نجمة ولكن لديك {u['stars']} ⭐")
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

    update.message.reply_text(
        f"✅ تم خصم {PRICE_STARS} نجمة من رصيدك.\n"
        f"💬 أرسل الآن ID لعبة Free Fire الخاص بك لكي أرسله لصاحب البوت."
    )

def handle_message(update: Update, context: CallbackContext):
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
        update.message.reply_text(f"🎉 تم استلام ID الخاص بك ({text}).\nسيقوم صاحب البوت بإضافة {amount} لايك قريباً.")

        # إرسال إشعار لصاحب البوت
        context.bot.send_message(
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
        update.message.reply_text("📌 رسالتك تم استلامها. إذا أردت شراء لايكات استخدم /buy.")

# ----- أمر إداري لإضافة نجوم -----
@owner_only
def add_stars(update: Update, context: CallbackContext):
    args = context.args
    if len(args) != 2:
        update.message.reply_text("استخدام: /addstars <user_id> <amount>")
        return
    try:
        target_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        update.message.reply_text("❌ القيم يجب أن تكون أرقام.")
        return

    ensure_user(target_id, None)
    u = get_user(target_id)
    new_balance = u["stars"] + amount
    update_stars(target_id, new_balance)
    update.message.reply_text(f"تمت إضافة {amount} ⭐ للمستخدم {target_id}. الرصيد الجديد: {new_balance} ⭐")

# ---------- تشغيل البوت ----------
def main():
    init_db()
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("buy", buy))
    dp.add_handler(CommandHandler("addstars", add_stars, pass_args=True))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("🚀 البوت يعمل الآن...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
