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

# ============= Settings ============
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
PROVIDER_TOKEN = ""  # فارغ للـ Telegram Stars
ORDERS_FILE = "orders.json"

# ضع رابط GitHub Pages هنا بعد النشر
WEBAPP_URL = "https://youcefmohamedelamine.github.io/winter_land_bot/"

PRODUCT_TITLE = "Buy Nothing"
PRODUCT_DESCRIPTION = "Buying literally nothing"
PAYLOAD = "buy_nothing"

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

def get_user_stats(user_id):
    """Get user statistics"""
    total_spent = get_total_spent(user_id)
    user_data = orders.get(user_id, {})
    history = user_data.get('history', [user_data] if user_data else [])
    order_count = len(history) if history and history[0] else 0
    rank = get_user_title(total_spent)
    
    return {
        'totalSpent': total_spent,
        'orderCount': order_count,
        'rank': rank
    }

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
    webapp_url = WEBAPP_URL
    
    if user_id:
        total = get_total_spent(user_id)
        title = get_user_title(total)
        
        # Encode user stats in URL for Web App
        stats = get_user_stats(user_id)
        import base64
        stats_encoded = base64.b64encode(json.dumps(stats).encode()).decode()
        webapp_url = f"{WEBAPP_URL}?data={stats_encoded}"
    
    keyboard = [
        [InlineKeyboardButton("🌟 افتح المتجر", web_app=WebAppInfo(url=webapp_url))],
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
    user_name = update.message.from_user.first_name
    
    try:
        data = json.loads(update.message.web_app_data.data)
        
        category = data.get('category')
        amount = data.get('amount')
        
        if data.get('action') == 'purchase' and category and amount:
            product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨", "description": "منتج حصري"})
            prices = [LabeledPrice(f"{product['name']}", amount)]
            
            # Send invoice
            await context.bot.send_invoice(
                chat_id=update.message.chat_id,
                title=f"{product['emoji']} {product['name']}",
                description=f"✨ {product['description']} - {amount:,} نجمة",
                payload=f"{PAYLOAD}_{category}_{amount}",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices
            )
            
            logger.info(f"Invoice sent to {user_name} ({user_id}): {product['name']} - {amount} stars")
    
    except Exception as e:
        logger.error(f"Error handling web app data: {e}")
        await update.message.reply_text("❌ حدث خطأ! حاول مرة أخرى.")

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
    product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨", "description": "منتج حصري"})

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
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    logger.info("🚀 Bot is running with Web App interface (No Flask needed)...")
    logger.info(f"📱 Web App URL: {WEBAPP_URL}")
    app.run_polling()

if __name__ == "__main__":
    main()
