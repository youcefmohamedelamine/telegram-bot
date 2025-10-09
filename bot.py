import logging
import os
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, render_template_string, request, jsonify
import threading
import json
from database import db

# إعدادات البوت
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://winterlandbot-production.up.railway.app")
PORT = int(os.getenv("PORT", 5000))

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask للواجهة الويب
app = Flask(__name__)

# صفحة HTML للويب أب
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>لعبة العملات</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            overflow-x: hidden;
        }

        .container {
            max-width: 500px;
            width: 100%;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 30px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.5s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .user-info {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-bottom: 20px;
        }

        .avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
        }

        .username {
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }

        .balance-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            color: white;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }

        .balance-label {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 10px;
        }

        .balance-amount {
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 10px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .tap-button {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            border: none;
            font-size: 80px;
            cursor: pointer;
            box-shadow: 0 15px 40px rgba(255, 215, 0, 0.5);
            transition: all 0.1s;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 30px auto;
        }

        .tap-button:active {
            transform: scale(0.95);
            box-shadow: 0 10px 30px rgba(255, 215, 0, 0.6);
        }

        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }

        .stat-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 8px;
        }

        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }

        .action-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }

        .action-btn {
            padding: 15px;
            border: none;
            border-radius: 15px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            color: white;
        }

        .action-btn.primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
        }

        .action-btn.secondary {
            background: linear-gradient(135deg, #f093fb, #f5576c);
        }

        .action-btn:active {
            transform: scale(0.95);
        }

        .floating-coin {
            position: fixed;
            font-size: 30px;
            pointer-events: none;
            animation: floatUp 1s ease-out forwards;
            z-index: 1000;
        }

        @keyframes floatUp {
            to {
                transform: translateY(-100px);
                opacity: 0;
            }
        }

        .energy-bar {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
        }

        .energy-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ade80, #22c55e);
            transition: width 0.3s;
            border-radius: 10px;
        }

        .energy-text {
            text-align: center;
            margin-top: 5px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="user-info">
                <div class="avatar" id="avatar">👤</div>
                <div class="username" id="username">مرحباً!</div>
            </div>
        </div>

        <div class="balance-card">
            <div class="balance-label">رصيدك</div>
            <div class="balance-amount" id="balance">0</div>
            <div style="font-size: 14px; opacity: 0.8;">عملة 💎</div>
        </div>

        <button class="tap-button" id="tapButton" onclick="tap()">
            🪙
        </button>

        <div class="energy-bar">
            <div class="energy-fill" id="energyFill" style="width: 100%;"></div>
        </div>
        <div class="energy-text" id="energyText">⚡ الطاقة: 1000/1000</div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">النقرات اليوم</div>
                <div class="stat-value" id="tapsToday">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">المستوى</div>
                <div class="stat-value" id="level">1</div>
            </div>
        </div>

        <div class="action-buttons">
            <button class="action-btn primary" onclick="showTasks()">📋 المهام</button>
            <button class="action-btn secondary" onclick="showFriends()">👥 الأصدقاء</button>
        </div>
    </div>

    <script>
        let balance = 0;
        let tapsToday = 0;
        let energy = 1000;
        let maxEnergy = 1000;
        let level = 1;
        let tapPower = 1;
        let userId = null;
        let saveInterval = null;

        // تهيئة Telegram WebApp
        let tg = window.Telegram.WebApp;
        tg.expand();
        tg.enableClosingConfirmation();

        // الحصول على معلومات المستخدم
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            let user = tg.initDataUnsafe.user;
            userId = user.id;
            document.getElementById('username').textContent = user.first_name || 'مستخدم';
            if (user.first_name) {
                document.getElementById('avatar').textContent = user.first_name.charAt(0).toUpperCase();
            }
            
            // تحميل البيانات من الخادم
            loadDataFromServer();
        }

        // تحميل البيانات من الخادم
        async function loadDataFromServer() {
            try {
                const response = await fetch('/api/user/' + userId);
                if (response.ok) {
                    const data = await response.json();
                    balance = data.balance || 0;
                    tapsToday = data.taps_today || 0;
                    energy = data.energy || 1000;
                    level = data.level || 1;
                    tapPower = data.tap_power || 1;
                    updateDisplay();
                }
            } catch (error) {
                console.error('خطأ في تحميل البيانات:', error);
            }
        }

        // حفظ البيانات على الخادم
        async function saveDataToServer() {
            if (!userId) return;
            
            try {
                await fetch('/api/save', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: userId,
                        balance: balance,
                        taps_today: tapsToday,
                        energy: energy,
                        level: level,
                        tap_power: tapPower
                    })
                });
            } catch (error) {
                console.error('خطأ في حفظ البيانات:', error);
            }
        }

        function tap() {
            if (energy < tapPower) {
                tg.showAlert('⚠️ ليس لديك طاقة كافية! انتظر قليلاً...');
                return;
            }

            balance += tapPower;
            tapsToday += 1;
            energy -= tapPower;

            updateDisplay();
            createFloatingCoin(event);

            // ترقية المستوى
            if (balance >= level * 100) {
                level++;
                tapPower++;
                tg.showPopup({
                    title: '🎉 تهانينا!',
                    message: `وصلت للمستوى ${level}! قوة النقر الآن: ${tapPower}`,
                    buttons: [{type: 'ok'}]
                });
            }
        }

        function updateDisplay() {
            document.getElementById('balance').textContent = balance.toLocaleString();
            document.getElementById('tapsToday').textContent = tapsToday;
            document.getElementById('level').textContent = level;
            
            let energyPercent = (energy / maxEnergy) * 100;
            document.getElementById('energyFill').style.width = energyPercent + '%';
            document.getElementById('energyText').textContent = `⚡ الطاقة: ${energy}/${maxEnergy}`;
        }

        function createFloatingCoin(e) {
            let coin = document.createElement('div');
            coin.className = 'floating-coin';
            coin.textContent = '+' + tapPower;
            coin.style.left = e.clientX + 'px';
            coin.style.top = e.clientY + 'px';
            coin.style.color = '#ffd700';
            coin.style.fontWeight = 'bold';
            document.body.appendChild(coin);

            setTimeout(() => coin.remove(), 1000);
        }

        // استعادة الطاقة تلقائياً
        setInterval(() => {
            if (energy < maxEnergy) {
                energy = Math.min(energy + 1, maxEnergy);
                updateDisplay();
            }
        }, 1000);

        // حفظ البيانات كل 5 ثواني
        setInterval(() => {
            saveDataToServer();
        }, 5000);

        // حفظ عند إغلاق الصفحة
        window.addEventListener('beforeunload', () => {
            saveDataToServer();
        });

        function showTasks() {
            tg.showPopup({
                title: '📋 المهام اليومية',
                message: '• انقر 100 مرة: +500 💎\n• ادعُ 3 أصدقاء: +1000 💎\n• افتح التطبيق 7 أيام: +5000 💎',
                buttons: [{type: 'ok'}]
            });
        }

        function showFriends() {
            tg.showPopup({
                title: '👥 ادعُ أصدقائك',
                message: 'احصل على 500 💎 عن كل صديق يشترك!\n\nشارك رابط الدعوة مع أصدقائك.',
                buttons: [
                    {type: 'default', text: 'مشاركة'},
                    {type: 'cancel'}
                ]
            });
        }

        updateDisplay();
    </script>
</body>
</html>
"""

@app.route('/')
def webapp():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    """API للحصول على بيانات المستخدم"""
    user = db.get_user(user_id)
    if user:
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/save', methods=['POST'])
def save_game_data():
    """API لحفظ بيانات اللعبة"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        db.update_game_data(
            user_id=user_id,
            balance=data.get('balance'),
            taps_today=data.get('taps_today'),
            energy=data.get('energy'),
            level=data.get('level'),
            tap_power=data.get('tap_power')
        )
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"خطأ في حفظ البيانات: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaderboard')
def leaderboard():
    """API للحصول على المتصدرين"""
    leaders = db.get_leaderboard(limit=10)
    return jsonify(leaders)

# دوال البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب مع زر فتح التطبيق"""
    user = update.effective_user
    
    # حفظ/تحديث بيانات المستخدم في قاعدة البيانات
    invited_by = context.args[0] if context.args else None
    db.create_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        invited_by=invited_by
    )
    
    keyboard = [
        [InlineKeyboardButton("🎮 العب الآن", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        f"🎉 مرحباً {user.first_name}!\n\n"
        "🪙 اجمع العملات واحصل على مكافآت رائعة!\n"
        "💎 انقر على الزر أدناه لبدء اللعب\n\n"
        "📊 المميزات:\n"
        "• نقرات غير محدودة\n"
        "• نظام المستويات\n"
        "• مهام يومية\n"
        "• دعوة الأصدقاء\n\n"
        f"🔗 رابط الدعوة الخاص بك:\n"
        f"https://t.me/YOUR_BOT_USERNAME?start={user.id}"
    )
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المساعدة"""
    help_text = (
        "📱 كيف تلعب:\n\n"
        "1️⃣ اضغط على زر 'العب الآن'\n"
        "2️⃣ انقر على العملة لجمع النقاط\n"
        "3️⃣ أكمل المهام للحصول على مكافآت\n"
        "4️⃣ ادعُ أصدقائك واحصل على مكافآت إضافية\n\n"
        "💡 نصيحة: كلما زاد مستواك، زادت النقاط من كل نقرة!"
    )
    await update.message.reply_text(help_text)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات اللاعب"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    if user_data:
        stats_text = (
            f"📊 إحصائياتك:\n\n"
            f"👤 الاسم: {user.first_name}\n"
            f"🆔 المعرف: {user.id}\n"
            f"💎 الرصيد: {user_data['balance']:,}\n"
            f"⭐ المستوى: {user_data['level']}\n"
            f"👥 عدد الأصدقاء: {user_data['invited_count']}\n"
            f"📅 انضممت: {user_data['created_at'].strftime('%Y-%m-%d')}"
        )
    else:
        stats_text = (
            f"📊 إحصائياتك:\n\n"
            f"👤 الاسم: {user.first_name}\n"
            f"🆔 المعرف: {user.id}\n\n"
            "افتح اللعبة لمشاهدة رصيدك الكامل! 🎮"
        )
    
    keyboard = [
        [InlineKeyboardButton("🎮 افتح اللعبة", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(stats_text, reply_markup=reply_markup)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة المتصدرين"""
    leaders = db.get_leaderboard(limit=10)
    
    if not leaders:
        await update.message.reply_text("📊 لا يوجد متصدرين حتى الآن!")
        return
    
    leaderboard_text = "🏆 قائمة المتصدرين:\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    for idx, leader in enumerate(leaders):
        medal = medals[idx] if idx < 3 else f"{idx + 1}."
        name = leader['first_name'] or leader['username'] or 'لاعب'
        leaderboard_text += f"{medal} {name}\n"
        leaderboard_text += f"   💎 {leader['balance']:,} | ⭐ المستوى {leader['level']}\n\n"
    
    await update.message.reply_text(leaderboard_text)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات للمشرفين (ضع معرف المشرف هنا)"""
    ADMIN_IDS = [123456789]  # ضع معرفك هنا
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط!")
        return
    
    total_users = db.get_user_count()
    all_users = db.get_all_users()
    
    total_balance = sum(user['balance'] for user in all_users)
    active_today = sum(1 for user in all_users 
                      if user['last_active'].date() == datetime.now().date())
    
    stats_text = (
        "👑 إحصائيات المشرف:\n\n"
        f"👥 إجمالي المستخدمين: {total_users}\n"
        f"✅ نشط اليوم: {active_today}\n"
        f"💎 إجمالي العملات: {total_balance:,}\n"
    )
    
    await update.message.reply_text(stats_text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة جماعية (للمشرفين فقط)"""
    ADMIN_IDS = [123456789]  # ضع معرفك هنا
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 استخدم: /broadcast <الرسالة>\n"
            "مثال: /broadcast مرحباً بالجميع!"
        )
        return
    
    message = ' '.join(context.args)
    all_users = db.get_all_users()
    
    success = 0
    failed = 0
    
    for user in all_users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 رسالة من الإدارة:\n\n{message}"
            )
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"فشل إرسال الرسالة إلى {user['user_id']}: {e}")
    
    await update.message.reply_text(
        f"✅ تم إرسال الرسالة\n\n"
        f"نجح: {success}\n"
        f"فشل: {failed}"
    )

def run_flask():
    """تشغيل خادم Flask"""
    app.run(host='0.0.0.0', port=PORT, debug=False)

def main():
    """تشغيل البوت"""
    # تشغيل Flask في خيط منفصل
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("admin", admin_stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    
    # بدء البوت
    logger.info("🚀 البوت يعمل الآن...")
    logger.info(f"📊 عدد المستخدمين في قاعدة البيانات: {db.get_user_count()}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
