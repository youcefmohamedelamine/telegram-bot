import logging
import json
import os
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice
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
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
ORDERS_FILE = "orders.json"

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
    """Get user title based on total amount spent"""
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
    """Calculate total amount spent by user"""
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
        "emoji": "🔹",
        "prices": [
            {"label": "5,000 ⭐", "amount": 5000},
            {"label": "10,000 ⭐", "amount": 10000},
            {"label": "15,000 ⭐", "amount": 15000}
        ]
    },
    "medium": {
        "name": "🔷 لاشيء متوسط",
        "description": "الخيار الأكثر شعبية",
        "emoji": "🔷",
        "prices": [
            {"label": "20,000 ⭐", "amount": 20000},
            {"label": "30,000 ⭐", "amount": 30000},
            {"label": "40,000 ⭐", "amount": 40000}
        ]
    },
    "large": {
        "name": "💠 لاشيء كبير",
        "description": "للمحترفين فقط",
        "emoji": "💠",
        "prices": [
            {"label": "50,000 ⭐", "amount": 50000},
            {"label": "75,000 ⭐", "amount": 75000},
            {"label": "100,000 ⭐", "amount": 100000}
        ]
    }
}

# ============= Beautiful Main Menu ============
def main_menu(user_id=None):
    title = ""
    if user_id:
        total = get_total_spent(user_id)
        title = get_user_title(total)
    
    keyboard = [
        [InlineKeyboardButton("🛍️ تصفح المنتجات", callback_data="browse_products")],
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

# ============= Calculate Total Stats ============
def get_stats():
    total_orders = sum(len(user_data.get('history', [])) if isinstance(user_data, dict) and 'history' in user_data else 1 for user_data in orders.values())
    total_revenue = sum(get_total_spent(user_id) for user_id in orders.keys())
    return total_orders, total_revenue

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

🎭 اختر من منتجاتنا الحصرية:
🔹 *لاشيء صغير* - للمبتدئين
🔷 *لاشيء متوسط* - الأكثر مبيعاً
💠 *لاشيء كبير* - للمحترفين

💫 كل عملية شراء تقربك من لقب أعلى!

⬇️ اختر من القائمة:
"""
    await update.message.reply_text(
        welcome_message,
        reply_markup=menu_markup,
        parse_mode="Markdown"
    )

# ============= Button Handler ============
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == "browse_products":
        browse_message = """
╭━━━━━━━━━━━━━━━━━━━╮
┃  🛍️ تصفح المنتجات  ┃
╰━━━━━━━━━━━━━━━━━━━╯

اختر الفئة المناسبة لك:

🔹 *لاشيء صغير*
   └ مثالي للبداية
   └ 5K - 15K ⭐

🔷 *لاشيء متوسط*  
   └ الأكثر شعبية
   └ 20K - 40K ⭐

💠 *لاشيء كبير*
   └ للمحترفين فقط
   └ 50K - 100K ⭐

━━━━━━━━━━━━━━━━
⬇️ اختر الفئة:
"""
        keyboard = [
            [InlineKeyboardButton("🔹 لاشيء صغير", callback_data="cat_small")],
            [InlineKeyboardButton("🔷 لاشيء متوسط", callback_data="cat_medium")],
            [InlineKeyboardButton("💠 لاشيء كبير", callback_data="cat_large")],
            [InlineKeyboardButton("« رجوع", callback_data="back")]
        ]
        await query.edit_message_text(
            browse_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data.startswith("cat_"):
        category = query.data.replace("cat_", "")
        product = PRODUCTS[category]
        
        category_message = f"""
╭━━━━━━━━━━━━━━━━━━━╮
┃  {product['emoji']} {product['name']}  ┃
╰━━━━━━━━━━━━━━━━━━━╯

📦 *الوصف:* {product['description']}

✨ المميزات:
  • جودة عالية من العدم
  • تسليم فوري 100%
  • ضمان اللاوجود
  • دعم فني 24/7

━━━━━━━━━━━━━━━━
💰 اختر السعر المناسب:
"""
        keyboard = []
        for price_option in product['prices']:
            keyboard.append([
                InlineKeyboardButton(
                    f"{product['emoji']} {price_option['label']}",
                    callback_data=f"buy_{category}_{price_option['amount']}"
                )
            ])
        keyboard.append([InlineKeyboardButton("« رجوع للفئات", callback_data="browse_products")])
        
        await query.edit_message_text(
            category_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data.startswith("buy_"):
        parts = query.data.split("_")
        category = parts[1]
        amount = int(parts[2])
        product = PRODUCTS[category]
        
        prices = [LabeledPrice(f"{product['name']}", amount)]
        
        await query.edit_message_text(
            f"🎯 اخترت: *{product['name']}*\n"
            f"💰 السعر: *{amount:,} ⭐*\n\n"
            f"⏳ جاري تجهيز الفاتورة...",
            parse_mode="Markdown"
        )
        
        await context.bot.send_invoice(
            chat_id=query.from_user.id,
            title=f"{product['emoji']} {product['name']}",
            description=f"✨ {product['description']} - {amount:,} نجمة",
            payload=f"{PAYLOAD}_{category}_{amount}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )

    elif query.data == "my_info":
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

🎁 ابدأ رحلتك في عالم اللاشيء!
💫 اشترِ الآن واحصل على لقبك الأول
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
        
        # Calculate next rank
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
        total_orders, total_revenue = get_stats()
        
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
    
    # Parse payload to get category
    payload_parts = payment_info.invoice_payload.split("_")
    category = payload_parts[2] if len(payload_parts) > 2 else "unknown"
    product = PRODUCTS.get(category, {"name": "لاشيء", "emoji": "✨"})

    # Create order record
    new_order = {
        "time": datetime.now().isoformat(),
        "amount": payment_info.total_amount,
        "status": "completed",
        "username": update.message.from_user.username or "Unknown",
        "category": category,
        "product": product['name']
    }

    # Save order with history
    if user_id in orders:
        if 'history' not in orders[user_id]:
            # Convert old format to new format
            old_order = orders[user_id].copy()
            orders[user_id] = {'history': [old_order, new_order]}
        else:
            orders[user_id]['history'].append(new_order)
    else:
        orders[user_id] = {'history': [new_order]}
    
    save_orders()

    # Calculate new title
    total_spent = get_total_spent(user_id)
    old_total = total_spent - payment_info.total_amount
    old_title = get_user_title(old_total)
    new_title = get_user_title(total_spent)
    
    rank_up_msg = ""
    if old_title != new_title:
        rank_up_msg = f"\n\n🎊 *تهانينا! ترقية اللقب!*\n{old_title} ➜ {new_title}"

    # Beautiful success message
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

    # Notify admin
    total_orders, total_revenue = get_stats()
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
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    logger.info("🚀 Bot is running with products scroll view and rank system...")
    app.run_polling()

if __name__ == "__main__":
    main()
