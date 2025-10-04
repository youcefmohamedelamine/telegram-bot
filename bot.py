import logging
import json
import os
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    WebAppInfo
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    ContextTypes,
    filters
)
from flask import Flask, render_template_string, request, jsonify
import threading

# ============= Settings ============
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
ORDERS_FILE = "orders.json"
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")  # رابط الـ Web App

PRODUCT_TITLE = "Buy Nothing"
PRODUCT_DESCRIPTION = "Buying literally nothing"
PAYLOAD = "buy_nothing"

# ============= Flask App for Web Interface ============
flask_app = Flask(__name__)

# ============= Web App HTML ============
WEBAPP_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجر اللاشيء</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            overflow-x: hidden;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            padding: 30px 0;
            animation: fadeInDown 0.8s;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .profile-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            animation: fadeInUp 0.8s;
        }
        
        .profile-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .avatar {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2em;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .profile-info h2 {
            font-size: 1.5em;
            margin-bottom: 5px;
        }
        
        .rank-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 15px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            display: block;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .products-section {
            margin: 30px 0;
            animation: fadeInUp 1s;
        }
        
        .section-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .product-grid {
            display: grid;
            gap: 20px;
        }
        
        .product-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }
        
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
        }
        
        .product-card:active {
            transform: translateY(-2px);
        }
        
        .product-icon {
            font-size: 3em;
            text-align: center;
            margin-bottom: 15px;
        }
        
        .product-name {
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }
        
        .product-description {
            text-align: center;
            opacity: 0.9;
            margin-bottom: 15px;
        }
        
        .price-options {
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .price-btn {
            background: rgba(255, 255, 255, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.5);
            padding: 10px 20px;
            border-radius: 15px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .price-btn:hover {
            background: rgba(255, 255, 255, 0.5);
            transform: scale(1.05);
        }
        
        .rank-progress {
            margin: 30px 0;
            animation: fadeInUp 1.2s;
        }
        
        .progress-bar {
            background: rgba(255, 255, 255, 0.2);
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
            height: 100%;
            transition: width 1s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .next-rank {
            text-align: center;
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .floating {
            animation: floating 3s ease-in-out infinite;
        }
        
        @keyframes floating {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-10px);
            }
        }
        
        .purchase-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 20px;
            max-width: 400px;
            width: 90%;
            text-align: center;
            animation: fadeInUp 0.5s;
        }
        
        .modal-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        
        .modal-buttons {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }
        
        .btn {
            flex: 1;
            padding: 15px;
            border-radius: 15px;
            border: none;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-confirm {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        
        .btn-cancel {
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }
        
        .btn:hover {
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header floating">
            <h1>🌟 متجر اللاشيء 🌟</h1>
            <p class="subtitle">امتلك العدم بأفضل الأسعار</p>
        </div>
        
        <div class="profile-card">
            <div class="profile-header">
                <div class="avatar">👤</div>
                <div class="profile-info">
                    <h2 id="userName">مرحباً</h2>
                    <span class="rank-badge" id="userRank">🌱 زائر جديد</span>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-value" id="totalSpent">0</span>
                    <span class="stat-label">⭐ إجمالي الإنفاق</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value" id="orderCount">0</span>
                    <span class="stat-label">📦 الطلبات</span>
                </div>
            </div>
        </div>
        
        <div class="rank-progress">
            <div class="progress-bar">
                <div class="progress-fill" id="progressBar" style="width: 0%">
                    <span id="progressText">0%</span>
                </div>
            </div>
            <p class="next-rank" id="nextRank">🎯 اللقب القادم: مبتدئ اللاشيء</p>
        </div>
        
        <div class="products-section">
            <h2 class="section-title">🛍️ المنتجات المتاحة</h2>
            <div class="product-grid">
                <div class="product-card" onclick="selectProduct('small')">
                    <div class="product-icon">🔹</div>
                    <div class="product-name">لاشيء صغير</div>
                    <p class="product-description">مثالي للمبتدئين</p>
                    <div class="price-options">
                        <button class="price-btn" onclick="event.stopPropagation(); showPurchaseModal('small', 5000)">5K ⭐</button>
                        <button class="price-btn" onclick="event.stopPropagation(); showPurchaseModal('small', 10000)">10K ⭐</button>
                        <button class="price-btn" onclick="event.stopPropagation(); showPurchaseModal('small', 15000)">15K ⭐</button>
                    </div>
                </div>
                
                <div class="product-card" onclick="selectProduct('medium')">
                    <div class="product-icon">🔷</div>
                    <div class="product-name">لاشيء متوسط</div>
                    <p class="product-description">الأكثر شعبية</p>
                    <div class="price-options">
                        <button class="price-btn" onclick="event.stopPropagation(); showPurchaseModal('medium', 20000)">20K ⭐</button>
                        <button class="price-btn" onclick="event.stopPropagation(); showPurchaseModal('medium', 30000)">30K ⭐</button>
                        <button class="price-btn" onclick="event.stopPropagation(); showPurchaseModal('medium', 40000)">40K ⭐</button>
                    </div>
                </div>
                
                <div class="product-card" onclick="selectProduct('large')">
                    <div class="product-icon">💠</div>
                    <div class="product-name">لاشيء كبير</div>
                    <p class="product-description">للمحترفين فقط</p>
                    <div class="price-options">
                        <button class="price-btn" onclick="event.stopPropagation(); showPurchaseModal('large', 50000)">50K ⭐</button>
                        <button class="price-btn" onclick="event.stopPropagation(); showPurchaseModal('large', 75000)">75K ⭐</button>
                        <button class="price-btn" onclick="event.stopPropagation(); showPurchaseModal('large', 100000)">100K ⭐</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="purchase-modal" id="purchaseModal">
        <div class="modal-content">
            <div class="modal-icon">✨</div>
            <h2 id="modalTitle">تأكيد الشراء</h2>
            <p id="modalText">هل أنت متأكد من شراء هذا المنتج؟</p>
            <div class="modal-buttons">
                <button class="btn btn-cancel" onclick="closePurchaseModal()">إلغاء</button>
                <button class="btn btn-confirm" onclick="confirmPurchase()">تأكيد</button>
            </div>
        </div>
    </div>
    
    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();
        
        let selectedCategory = '';
        let selectedAmount = 0;
        
        // Load user data
        function loadUserData() {
            const userId = tg.initDataUnsafe?.user?.id || 'demo';
            const userName = tg.initDataUnsafe?.user?.first_name || 'مستخدم تجريبي';
            
            document.getElementById('userName').textContent = userName;
            
            // Simulate loading user stats (في التطبيق الحقيقي، تحصل عليها من API)
            fetch('/api/user/' + userId)
                .then(res => res.json())
                .then(data => {
                    updateUserInterface(data);
                })
                .catch(() => {
                    // Demo data
                    updateUserInterface({
                        totalSpent: 0,
                        orderCount: 0,
                        rank: '🌱 زائر جديد'
                    });
                });
        }
        
        function updateUserInterface(data) {
            document.getElementById('totalSpent').textContent = (data.totalSpent || 0).toLocaleString();
            document.getElementById('orderCount').textContent = data.orderCount || 0;
            document.getElementById('userRank').textContent = data.rank || '🌱 زائر جديد';
            
            // Calculate progress
            const ranks = [
                {threshold: 10000, name: '🎯 مبتدئ اللاشيء'},
                {threshold: 20000, name: '✨ تاجر العدم'},
                {threshold: 50000, name: '🌟 فارس اللاشيء'},
                {threshold: 100000, name: '⭐ نبيل العدم'},
                {threshold: 200000, name: '🏆 أمير الفراغ'},
                {threshold: 300000, name: '💎 ملك اللاشيء'},
                {threshold: 500000, name: '👑 إمبراطور العدم'}
            ];
            
            let nextRank = ranks[0];
            for (let rank of ranks) {
                if (data.totalSpent < rank.threshold) {
                    nextRank = rank;
                    break;
                }
            }
            
            const progress = Math.min((data.totalSpent / nextRank.threshold) * 100, 100);
            document.getElementById('progressBar').style.width = progress + '%';
            document.getElementById('progressText').textContent = Math.round(progress) + '%';
            document.getElementById('nextRank').textContent = 
                data.totalSpent >= 500000 ? '🎉 وصلت لأعلى لقب!' : 
                `🎯 اللقب القادم: ${nextRank.name}`;
        }
        
        function selectProduct(category) {
            console.log('Selected:', category);
        }
        
        function showPurchaseModal(category, amount) {
            selectedCategory = category;
            selectedAmount = amount;
            
            const names = {
                'small': '🔹 لاشيء صغير',
                'medium': '🔷 لاشيء متوسط',
                'large': '💠 لاشيء كبير'
            };
            
            document.getElementById('modalTitle').textContent = 'تأكيد الشراء';
            document.getElementById('modalText').textContent = 
                `هل تريد شراء ${names[category]} مقابل ${amount.toLocaleString()} ⭐؟`;
            
            document.getElementById('purchaseModal').style.display = 'flex';
        }
        
        function closePurchaseModal() {
            document.getElementById('purchaseModal').style.display = 'none';
        }
        
        function confirmPurchase() {
            tg.sendData(JSON.stringify({
                category: selectedCategory,
                amount: selectedAmount,
                action: 'purchase'
            }));
            closePurchaseModal();
        }
        
        // Initialize
        loadUserData();
        
        // Set theme colors
        tg.setHeaderColor('#667eea');
        tg.setBackgroundColor('#667eea');
    </script>
</body>
</html>
"""

@flask_app.route('/')
def webapp():
    return render_template_string(WEBAPP_HTML)

@flask_app.route('/api/user/<user_id>')
def get_user_data(user_id):
    user_data = orders.get(user_id, {})
    total_spent = get_total_spent(user_id)
    rank = get_user_title(total_spent)
    
    history = user_data.get('history', [user_data] if user_data else [])
    order_count = len(history)
    
    return jsonify({
        'totalSpent': total_spent,
        'orderCount': order_count,
        'rank': rank
    })

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000)

# ============= Logging ============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= Load Orders ============
orders = {}
try:
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            orders = json.load(f)
except json.JSONDecodeError:
    orders = {}

def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

# ============= Title System ============
def get_user_title(total_spent):
    if total_spent >= 500000:
        return "👑 إمبراطور العدم"
    elif total_spent >= 300000:
        return "💎 ملك اللاشيء"
    elif total_spent >= 200000:
        return "🏆 أمير الفراغ"
    elif total_spent >= 100000:
        return "⭐ نبيل العدم"
    elif total_spent >= 50000:
        return "🌟 فارس اللاشيء"
    elif total_spent >= 20000:
        return "✨ تاجر العدم"
    elif total_spent >= 10000:
        return "🎯 مبتدئ اللاشيء"
    else:
        return "🌱 زائر جديد"

def get_total_spent(user_id):
    user_orders = orders.get(user_id, {})
    if isinstance(user_orders, dict) and 'history' in user_orders:
        return sum(order.get('amount', 0) for order in user_orders['history'])
    elif isinstance(user_orders, dict) and 'amount' in user_orders:
        return user_orders.get('amount', 0)
    return 0

# ============= Product Categories ============
PRODUCTS = {
    "small": {
        "name": "🔹 لاشيء صغير",
        "description": "حجم مثالي للمبتدئين",
        "emoji": "🔹"
    },
    "medium": {
        "name": "🔷 لاشيء متوسط",
        "description": "الخيار الأكثر شعبية",
        "emoji": "🔷"
    },
    "large": {
        "name": "💠 لاشيء كبير",
        "description": "للمحترفين فقط",
        "emoji": "💠"
    }
}

# ============= Main Menu with Web App ============
def main_menu(user_id=None):
    title = ""
    if user_id:
        total = get_total_spent(user_id)
        title = get_user_title(total)
    
    keyboard = [
        [InlineKeyboardButton("🌟 افتح المتجر", web_app=WebAppInfo(url=WEBAPP_URL))],
        [
            InlineKeyboardButton("👤 حسابي", callback_data="my_info"),
            InlineKeyboardButton("🏆 لقبي", callback_data="my_rank")
        ],
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"),
            InlineKeyboardButton("💬 تواصل معنا", callback_data="contact")
        ]
    ]
    return InlineKeyboardMarkup(keyboard), title

# ============= /start ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    user_id = str(update.message.from_user.id)
    
    menu_markup, user_title = main_menu(user_id)
    
    welcome_message = f"""
╔══════════════════════╗
║   🌟 متجر اللاشيء 🌟   ║
╚══════════════════════╝

مرحباً *{user_name}*! 👋
{user_title}

✨ *واجهة جديدة ومميزة!*

اضغط على "🌟 افتح المتجر" لتجربة:
• 🎨 تصميم عصري وجميل
• 📊 إحصائيات تفاعلية
• 🏆 نظام الألقاب المرئي
• 🛍️ تصفح سهل وسريع

⬇️ اختر من القائمة:
"""
    await update.message.reply_text(
        welcome_message,
        reply_markup=menu_markup,
        parse_mode="Markdown"
    )

# ============= Handle Web App Data ============
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = json.loads(update.message.web_app_data.data)
    
    category = data.get('category')
    amount = data.get('amount')
    
    if data.get('action') == 'purchase':
        product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨"})
        prices = [LabeledPrice(f"{product['name']}", amount)]
        
        await context.bot.send_invoice(
            chat_id=update.message.chat_id,
            title=f"{product['emoji']} {product['name']}",
            description=f"✨ {product['description']} - {amount:,} نجمة",
            payload=f"{PAYLOAD}_{category}_{amount}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )

# ============= Menu Handler (Buttons) ============
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == "my_info":
        total_spent = get_total_spent(user_id)
        user_title = get_user_title(total_spent)
        user_data = orders.get(user_id, {})
        
        if not user_data:
            info_message = f"""
╭━━━━━━━━━━━━━━━━╮
┃   👤 معلومات الحساب   ┃
╰━━━━━━━━━━━━━━━━╯

🏷️ *اللقب:* {user_title}
💰 *إجمالي الإنفاق:* 0 ⭐

❌ لم تقم بأي عملية شراء بعد

🎁 افتح المتجر وابدأ رحلتك!
"""
        else:
            history = user_data.get('history', [user_data])
            order_count = len(history)
            last_order = history[-1] if history else {}
            
            if last_order:
                order_time = datetime.fromisoformat(last_order.get('time', datetime.now().isoformat()))
                time_str = order_time.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = "غير متوفر"
            
            info_message = f"""
╭━━━━━━━━━━━━━━━━╮
┃   👤 معلومات الحساب   ┃
╰━━━━━━━━━━━━━━━━╯

🏷️ *اللقب الحالي:* {user_title}
💰 *إجمالي الإنفاق:* {total_spent:,} ⭐
📦 *عدد الطلبات:* {order_count}

━━━━━━━━━━━━━━━━
📋 *آخر عملية شراء:*

🕐 التاريخ: `{time_str}`
💵 المبلغ: *{last_order.get('amount', 0):,} ⭐*
✅ الحالة: *مكتمل*

━━━━━━━━━━━━━━━━
💎 استمر في الشراء للحصول على ألقاب أعلى!
"""
        
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data="back")]]
        await query.edit_message_text(
            info_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "my_rank":
        total_spent = get_total_spent(user_id)
        current_title = get_user_title(total_spent)
        
        ranks = [
            (10000, "🎯 مبتدئ اللاشيء"),
            (20000, "✨ تاجر العدم"),
            (50000, "🌟 فارس اللاشيء"),
            (100000, "⭐ نبيل العدم"),
            (200000, "🏆 أمير الفراغ"),
            (300000, "💎 ملك اللاشيء"),
            (500000, "👑 إمبراطور العدم")
        ]
        
        next_rank = None
        remaining = 0
        for threshold, title in ranks:
            if total_spent < threshold:
                next_rank = title
                remaining = threshold - total_spent
                break
        
        rank_message = f"""
╭━━━━━━━━━━━━━━━━╮
┃   🏆 نظام الألقاب   ┃
╰━━━━━━━━━━━━━━━━╯

🎖️ *لقبك الحالي:*
{current_title}

💰 *إجمالي إنفاقك:* {total_spent:,} ⭐

━━━━━━━━━━━━━━━━
📊 *جدول الألقاب:*

🌱 زائر جديد: 0+ ⭐
🎯 مبتدئ اللاشيء: 10K+ ⭐
✨ تاجر العدم: 20K+ ⭐
🌟 فارس اللاشيء: 50K+ ⭐
⭐ نبيل العدم: 100K+ ⭐
🏆 أمير الفراغ: 200K+ ⭐
💎 ملك اللاشيء: 300K+ ⭐
👑 إمبراطور العدم: 500K+ ⭐

━━━━━━━━━━━━━━━━
"""
        
        if next_rank:
            rank_message += f"🎯 *اللقب القادم:* {next_rank}\n💫 *تبقى:* {remaining:,} ⭐"
        else:
            rank_message += "🎉 *مبروك!* وصلت لأعلى لقب!"
        
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data="back")]]
        await query.edit_message_text(
            rank_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "stats":
        total_orders = sum(len(user_data.get('history', [])) if isinstance(user_data, dict) and 'history' in user_data else 1 for user_data in orders.values())
        total_revenue = sum(get_total_spent(uid) for uid in orders.keys())
        
        stats_message = f"""
╭━━━━━━━━━━━━━━━━╮
┃   📊 إحصائيات المتجر   ┃
╰━━━━━━━━━━━━━━━━╯

📦 إجمالي الطلبات: *{total_orders:,}*
💎 إجمالي الإيرادات: *{total_revenue:,} ⭐*
👥 عدد العملاء: *{len(orders):,}*
🏆 أكثر منتج مبيعاً: *اللاشيء*

━━━━━━━━━━━━━━━━
🌟 انضم لعائلتنا المتنامية!
🎯 كن جزءاً من الإحصائيات
"""
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data="back")]]
        await query.edit_message_text(
            stats_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "contact":
        contact_message = """
╭━━━━━━━━━━━━━━━━╮
┃   💬 تواصل معنا   ┃
╰━━━━━━━━━━━━━━━━╯

📞 *قنوات التواصل:*

👤 الدعم الفني: @YourSupportUsername
📧 البريد الإلكتروني: support@nothing.shop
🌐 الموقع: nothing-shop.com

⏰ نحن هنا لخدمتك 24/7
💬 سنرد عليك في أقرب وقت ممكن

━━━━━━━━━━━━━━━━
🌟 رضاك يهمنا
"""
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data="back")]]
        await query.edit_message_text(
            contact_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "back":
        user_name = query.from_user.first_name
        menu_markup, user_title = main_menu(user_id)
        
        welcome_back = f"""
╔══════════════════════╗
║   🌟 متجر اللاشيء 🌟   ║
╚══════════════════════╝

أهلاً بعودتك *{user_name}*! 👋
{user_title}

⬇️ اختر من القائمة:
"""
        await query.edit_message_text(
            welcome_back,
            reply_markup=menu_markup,
            parse_mode="Markdown"
        )

# ============= Precheckout ============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if not query.invoice_payload.startswith(PAYLOAD):
        await query.answer(ok=False, error_message="❌ حدث خطأ في عملية الدفع")
    else:
        await query.answer(ok=True)

# ============= Successful Payment ============
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_name = update.message.from_user.first_name
    payment_info = update.message.successful_payment
    
    payload_parts = payment_info.invoice_payload.split("_")
    category = payload_parts[2] if len(payload_parts) > 2 else "unknown"
    product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨"})

    new_order = {
        "time": datetime.now().isoformat(),
        "amount": payment_info.total_amount,
        "status": "completed",
        "username": update.message.from_user.username or "Unknown",
        "category": category,
        "product": product['name']
    }

    if user_id in orders:
        if 'history' not in orders[user_id]:
            old_order = orders[user_id].copy()
            orders[user_id] = {'history': [old_order, new_order]}
        else:
            orders[user_id]['history'].append(new_order)
    else:
        orders[user_id] = {'history': [new_order]}
    
    save_orders()

    total_spent = get_total_spent(user_id)
    old_total = total_spent - payment_info.total_amount
    old_title = get_user_title(old_total)
    new_title = get_user_title(total_spent)
    
    rank_up_msg = ""
    if old_title != new_title:
        rank_up_msg = f"\n\n🎊 *تهانينا! ترقية اللقب!*\n{old_title} ➜ {new_title}"

    success_message = f"""
╔══════════════════════╗
║   🎉 تهانينا! 🎉   ║
╚══════════════════════╝

عزيزي *{user_name}*،

✨ تم إتمام عملية الشراء بنجاح!

━━━━━━━━━━━━━━━━
📦 المنتج: *{product['name']}*
💰 المبلغ: *{payment_info.total_amount:,} ⭐*
📅 التاريخ: `{datetime.now().strftime("%Y-%m-%d %H:%M")}`
━━━━━━━━━━━━━━━━

🏷️ *لقبك الحالي:* {new_title}
💎 *إجمالي إنفاقك:* {total_spent:,} ⭐{rank_up_msg}

━━━━━━━━━━━━━━━━
🎁 مبروك! أنت الآن مالك رسمي للاشيء
💫 تم إضافة العدم إلى حسابك بنجاح
🌟 استمتع بتجربة اللاملموس

━━━━━━━━━━━━━━━━
شكراً لثقتك بنا! 💕
"""
    
    menu_markup, _ = main_menu(user_id)
    await update.message.reply_text(
        success_message,
        parse_mode="Markdown",
        reply_markup=menu_markup
    )

    total_orders = sum(len(user_data.get('history', [])) if isinstance(user_data, dict) and 'history' in user_data else 1 for user_data in orders.values())
    total_revenue = sum(get_total_spent(uid) for uid in orders.keys())
    admin_notification = f"""
╔══════════════════════╗
║   📢 طلب جديد!   ║
╚══════════════════════╝

👤 المستخدم: @{update.message.from_user.username or user_id}
📛 الاسم: {user_name}
🏷️ اللقب: {new_title}
📦 المنتج: {product['name']}
💰 المبلغ: *{payment_info.total_amount:,} ⭐*
🕐 الوقت: `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`

━━━━━━━━━━━━━━━━
🎯 إجمالي الطلبات: {total_orders}
💎 إجمالي الإيرادات: {total_revenue:,} ⭐
"""
    
    await context.bot.send_message(
        ADMIN_ID,
        admin_notification,
        parse_mode="Markdown"
    )

# ============= Run Bot ============
def main():
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    logger.info("🚀 Bot is running with beautiful Web App interface...")
    logger.info("🌐 Web App running on port 5000")
    app.run_polling()

if __name__ == "__main__":
    main()
