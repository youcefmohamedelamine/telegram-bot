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

# ============= Beautiful Main Menu ============
def main_menu():
    keyboard = [
        [InlineKeyboardButton("✨ متجر اللاشيء ✨", callback_data="buy_menu")],
        [
            InlineKeyboardButton("👤 حسابي", callback_data="my_info"),
            InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
        ],
        [InlineKeyboardButton("💬 تواصل معنا", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============= Calculate Total Stats ============
def get_stats():
    total_orders = len(orders)
    total_revenue = sum(order.get('amount', 0) for order in orders.values())
    return total_orders, total_revenue

# ============= /start ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    welcome_message = f"""
╔══════════════════════╗
║   🌟 متجر اللاشيء 🌟   ║
╚══════════════════════╝

مرحباً *{user_name}*! 👋

🎭 هنا يمكنك شراء *اللاشيء* بأفضل الأسعار!
💫 كل عملية شراء تمنحك شعوراً فريداً بامتلاك العدم
🌈 انضم لآلاف المشترين السعداء

⬇️ اختر من القائمة أدناه:
"""
    await update.message.reply_text(
        welcome_message,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ============= Button Handler ============
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == "buy_menu":
        buy_message = """
╭━━━━━━━━━━━━━━━━━━━╮
┃  💎 اختر باقتك المفضلة  ┃
╰━━━━━━━━━━━━━━━━━━━╯

🎯 كل الباقات تحتوي على *لاشيء* أصلي 100%
✅ ضمان الجودة مدى الحياة
🚀 تسليم فوري

⭐ اختر المبلغ:
"""
        keyboard = [
            [
                InlineKeyboardButton("💫 10,000 ⭐", callback_data="10000"),
                InlineKeyboardButton("🌟 20,000 ⭐", callback_data="20000")
            ],
            [
                InlineKeyboardButton("✨ 30,000 ⭐", callback_data="30000"),
                InlineKeyboardButton("⚡ 40,000 ⭐", callback_data="40000")
            ],
            [
                InlineKeyboardButton("🔥 50,000 ⭐", callback_data="50000"),
                InlineKeyboardButton("💥 60,000 ⭐", callback_data="60000")
            ],
            [
                InlineKeyboardButton("🌠 70,000 ⭐", callback_data="70000"),
                InlineKeyboardButton("🎆 80,000 ⭐", callback_data="80000")
            ],
            [
                InlineKeyboardButton("🎇 90,000 ⭐", callback_data="90000"),
                InlineKeyboardButton("👑 100,000 ⭐", callback_data="100000")
            ],
            [InlineKeyboardButton("« رجوع للقائمة الرئيسية", callback_data="back")]
        ]
        await query.edit_message_text(
            buy_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data in ["10000","20000","30000","40000","50000","60000","70000","80000","90000","100000"]:
        amount = int(query.data)
        prices = [LabeledPrice(PRODUCT_TITLE, amount)]
        
        # Send a confirmation message
        await query.edit_message_text(
            f"🎯 لقد اخترت باقة *{amount:,} ⭐*\n\n"
            f"💰 جاري تجهيز فاتورة الدفع...\n"
            f"⏳ انتظر قليلاً...",
            parse_mode="Markdown"
        )
        
        await context.bot.send_invoice(
            chat_id=query.from_user.id,
            title=f"🌟 {PRODUCT_TITLE}",
            description=f"✨ {PRODUCT_DESCRIPTION} - باقة {amount:,} نجمة",
            payload=PAYLOAD,
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )

    elif query.data == "my_info":
        user_orders = orders.get(user_id)
        
        if not user_orders:
            info_message = """
╭━━━━━━━━━━━━━━━━╮
┃   👤 معلومات الحساب   ┃
╰━━━━━━━━━━━━━━━━╯

❌ لم تقم بأي عملية شراء بعد

🎁 ابدأ رحلتك في عالم اللاشيء الآن!
💫 كن أول من يمتلك العدم الحصري
"""
        else:
            order_time = datetime.fromisoformat(user_orders.get('time', datetime.now().isoformat()))
            time_str = order_time.strftime("%Y-%m-%d %H:%M")
            
            info_message = f"""
╭━━━━━━━━━━━━━━━━╮
┃   👤 معلومات الحساب   ┃
╰━━━━━━━━━━━━━━━━╯

📋 *آخر عملية شراء:*

🕐 التاريخ: `{time_str}`
💰 المبلغ: *{user_orders.get('amount', 0):,} ⭐*
✅ الحالة: *{user_orders.get('status', 'مكتمل')}*

━━━━━━━━━━━━━━━━
🎉 شكراً لثقتك بمتجرنا!
💎 أنت الآن مالك معتمد للاشيء
"""
        
        keyboard = [[InlineKeyboardButton("« رجوع للقائمة الرئيسية", callback_data="back")]]
        await query.edit_message_text(
            info_message,
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
🏆 أكثر منتج مبيعاً: *اللاشيء*

━━━━━━━━━━━━━━━━
🌟 انضم لعائلتنا المتنامية!
🎯 كن جزءاً من الإحصائيات
"""
        keyboard = [[InlineKeyboardButton("« رجوع للقائمة الرئيسية", callback_data="back")]]
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
        keyboard = [[InlineKeyboardButton("« رجوع للقائمة الرئيسية", callback_data="back")]]
        await query.edit_message_text(
            contact_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "back":
        user_name = query.from_user.first_name
        welcome_back = f"""
╔══════════════════════╗
║   🌟 متجر اللاشيء 🌟   ║
╚══════════════════════╝

أهلاً بعودتك *{user_name}*! 👋

⬇️ اختر من القائمة:
"""
        await query.edit_message_text(
            welcome_back,
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )

# ============= Precheckout ============
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != PAYLOAD:
        await query.answer(ok=False, error_message="❌ حدث خطأ في عملية الدفع")
    else:
        await query.answer(ok=True)

# ============= Successful Payment ============
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_name = update.message.from_user.first_name
    payment_info = update.message.successful_payment

    # Save order
    orders[user_id] = {
        "time": datetime.now().isoformat(),
        "amount": payment_info.total_amount,
        "status": "completed",
        "username": update.message.from_user.username or "Unknown"
    }
    save_orders()

    # Beautiful success message
    success_message = f"""
╔══════════════════════╗
║   🎉 تهانينا! 🎉   ║
╚══════════════════════╝

عزيزي *{user_name}*،

✨ تم إتمام عملية الشراء بنجاح!

━━━━━━━━━━━━━━━━
📦 المنتج: *اللاشيء الحصري*
💰 المبلغ: *{payment_info.total_amount:,} ⭐*
📅 التاريخ: `{datetime.now().strftime("%Y-%m-%d %H:%M")}`
━━━━━━━━━━━━━━━━

🎁 مبروك! أنت الآن مالك رسمي للاشيء
💎 تم إضافة العدم إلى حسابك بنجاح
🌟 استمتع بتجربة اللاملموس

━━━━━━━━━━━━━━━━
شكراً لثقتك بنا! 💕
"""
    
    await update.message.reply_text(
        success_message,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

    # Notify admin with beautiful format
    admin_notification = f"""
╔══════════════════════╗
║   📢 طلب جديد!   ║
╚══════════════════════╝

👤 المستخدم: @{update.message.from_user.username or user_id}
📛 الاسم: {user_name}
💰 المبلغ: *{payment_info.total_amount:,} ⭐*
🕐 الوقت: `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`

━━━━━━━━━━━━━━━━
🎯 إجمالي الطلبات: {len(orders)}
💎 إجمالي الإيرادات: {sum(o.get('amount', 0) for o in orders.values()):,} ⭐
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

    logger.info("🚀 Bot is running with beautiful UI...")
    app.run_polling()

if __name__ == "__main__":
    main()
