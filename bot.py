import json
import os
from datetime import datetime
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, PreCheckoutQueryHandler, filters, ContextTypes, CallbackQueryHandler

# ============= إعدادات البوت =============
BOT_TOKEN = "7580086418:AAEE0shvKADPHNjaV-RyoBn0yO4IERyhUQQ"  # ضع توكن البوت هنا
PROVIDER_TOKEN = ""  # فارغ لأن نجوم تليجرام لا تحتاج provider token

class FreefireBot:
    def __init__(self):
        self.orders = self.load_orders()
        self.packages = {
            "100": {"stars": 10, "name": "100 نجمة فري فاير"},
            "310": {"stars": 30, "name": "310 نجمة فري فاير"},
            "520": {"stars": 50, "name": "520 نجمة فري فاير"},
            "1060": {"stars": 100, "name": "1060 نجمة فري فاير"},
            "2180": {"stars": 200, "name": "2180 نجمة فري فاير"}
        }
    
    def load_orders(self):
        """تحميل الطلبات من الملف"""
        try:
            if os.path.exists("orders.json"):
                with open("orders.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_orders(self):
        """حفظ الطلبات في الملف"""
        with open("orders.json", "w", encoding="utf-8") as f:
            json.dump(self.orders, f, indent=4, ensure_ascii=False)
    
    def create_order(self, user_id, package_id, stars_paid):
        """إنشاء طلب جديد"""
        self.orders[str(user_id)] = {
            "package": package_id,
            "freefire_id": "لم يُرسل",
            "stars_paid": stars_paid,
            "status": "waiting_id",
            "time": datetime.now().isoformat()
        }
        self.save_orders()
        return True
    
    def update_freefire_id(self, user_id, freefire_id):
        """تحديث Free Fire ID"""
        if str(user_id) in self.orders:
            self.orders[str(user_id)]["freefire_id"] = freefire_id
            self.orders[str(user_id)]["status"] = "processing"
            self.save_orders()
            return True
        return False
    
    def complete_order(self, user_id):
        """تحديد الطلب كمكتمل"""
        if str(user_id) in self.orders:
            self.orders[str(user_id)]["status"] = "completed"
            self.save_orders()
            return True
        return False
    
    def get_order(self, user_id):
        """الحصول على تفاصيل طلب"""
        return self.orders.get(str(user_id))


# إنشاء كائن البوت
bot_instance = FreefireBot()


# ============= معالجات البوت =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب"""
    keyboard = [
        [InlineKeyboardButton("🛒 شراء نجوم فري فاير", callback_data="buy")],
        [InlineKeyboardButton("📦 طلباتي", callback_data="my_orders")],
        [InlineKeyboardButton("ℹ️ المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🎮 *مرحباً بك في بوت فري فاير!*

✨ يمكنك شراء نجوم فري فاير بسهولة باستخدام نجوم تليجرام

🌟 *المميزات:*
• دفع آمن عبر نجوم تليجرام
• توصيل فوري خلال دقائق
• دعم فني 24/7

اختر ما تريد من القائمة أدناه 👇
    """
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def show_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الباقات المتاحة"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for package_id, package_info in bot_instance.packages.items():
        keyboard.append([
            InlineKeyboardButton(
                f"💎 {package_info['name']} - ⭐ {package_info['stars']} نجمة",
                callback_data=f"package_{package_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🛍️ *اختر الباقة المناسبة لك:*\n\n💫 الدفع عبر نجوم تليجرام",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def process_package_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار الباقة وإرسال فاتورة"""
    query = update.callback_query
    await query.answer()
    
    package_id = query.data.split("_")[1]
    package = bot_instance.packages.get(package_id)
    
    if not package:
        await query.edit_message_text("❌ حدث خطأ، يرجى المحاولة مرة أخرى")
        return
    
    # إرسال فاتورة الدفع بنجوم تليجرام
    title = f"💎 {package['name']}"
    description = f"شراء {package['name']} عبر نجوم تليجرام"
    payload = f"freefire_{package_id}_{query.from_user.id}"
    
    prices = [LabeledPrice(label=package['name'], amount=package['stars'])]
    
    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title=title,
        description=description,
        payload=payload,
        provider_token=PROVIDER_TOKEN,
        currency="XTR",  # عملة نجوم تليجرام
        prices=prices,
        start_parameter="freefire-payment"
    )
    
    await query.edit_message_text(
        f"✅ تم إنشاء فاتورة الدفع!\n\n"
        f"💎 الباقة: {package['name']}\n"
        f"⭐ السعر: {package['stars']} نجمة\n\n"
        f"اضغط على زر الدفع لإكمال العملية 👇"
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من الدفع قبل إتمامه"""
    query = update.pre_checkout_query
    
    # يمكنك إضافة فحوصات هنا إذا أردت
    await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الدفع الناجح"""
    payment = update.message.successful_payment
    user_id = update.message.from_user.id
    
    # استخراج معلومات الباقة من payload
    payload_parts = payment.invoice_payload.split("_")
    package_id = payload_parts[1]
    
    # إنشاء الطلب
    bot_instance.create_order(
        user_id=user_id,
        package_id=package_id,
        stars_paid=payment.total_amount
    )
    
    # طلب Free Fire ID
    await update.message.reply_text(
        "✅ *تم الدفع بنجاح!*\n\n"
        "🎮 الآن، يرجى إرسال *Free Fire ID* الخاص بك\n"
        "📱 مثال: 123456789\n\n"
        "⚡ سيتم توصيل النجوم خلال دقائق من إرسال الـ ID",
        parse_mode="Markdown"
    )


async def handle_freefire_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة استلام Free Fire ID"""
    user_id = update.message.from_user.id
    freefire_id = update.message.text.strip()
    
    # التحقق من وجود طلب بانتظار ID
    order = bot_instance.get_order(user_id)
    
    if not order:
        return
    
    if order.get("status") != "waiting_id":
        return
    
    # التحقق من صحة ID (أرقام فقط)
    if not freefire_id.isdigit() or len(freefire_id) < 8:
        await update.message.reply_text(
            "❌ Free Fire ID غير صحيح!\n\n"
            "يرجى إرسال رقم ID صحيح (8 أرقام أو أكثر)"
        )
        return
    
    # تحديث الطلب
    bot_instance.update_freefire_id(user_id, freefire_id)
    
    await update.message.reply_text(
        "✅ *تم استلام Free Fire ID بنجاح!*\n\n"
        f"🆔 ID: `{freefire_id}`\n"
        f"💎 الباقة: {bot_instance.packages[order['package']]['name']}\n\n"
        "⏳ جاري معالجة طلبك...\n"
        "🚀 سيتم توصيل النجوم خلال 5-10 دقائق\n\n"
        "📧 سنرسل لك إشعار عند اكتمال الطلب!",
        parse_mode="Markdown"
    )
    
    # هنا يمكنك إرسال إشعار للمسؤول لمعالجة الطلب يدوياً
    # أو ربطه بـ API لشحن تلقائي


async def show_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض طلبات المستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    order = bot_instance.get_order(user_id)
    
    if not order:
        await query.edit_message_text(
            "📦 *طلباتي*\n\n"
            "❌ ليس لديك أي طلبات حالياً\n\n"
            "🛒 ابدأ بشراء باقة الآن!",
            parse_mode="Markdown"
        )
        return
    
    status_emoji = {
        "waiting_id": "⏳",
        "processing": "🔄",
        "completed": "✅"
    }
    
    status_text = {
        "waiting_id": "بانتظار Free Fire ID",
        "processing": "قيد المعالجة",
        "completed": "مكتمل"
    }
    
    package_name = bot_instance.packages[order['package']]['name']
    
    text = f"""
📦 *طلبك الحالي:*

💎 الباقة: {package_name}
⭐ المدفوع: {order['stars_paid']} نجمة
🆔 Free Fire ID: `{order['freefire_id']}`
{status_emoji[order['status']]} الحالة: {status_text[order['status']]}
🕒 التاريخ: {datetime.fromisoformat(order['time']).strftime('%Y-%m-%d %H:%M')}
    """
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المساعدة"""
    query = update.callback_query
    await query.answer()
    
    help_text = """
ℹ️ *كيفية الاستخدام:*

1️⃣ اضغط على "شراء نجوم فري فاير"
2️⃣ اختر الباقة المناسبة
3️⃣ ادفع بنجوم تليجرام
4️⃣ أرسل Free Fire ID الخاص بك
5️⃣ انتظر 5-10 دقائق للتوصيل

💡 *ملاحظات مهمة:*
• تأكد من Free Fire ID قبل الإرسال
• النجوم تصل خلال 5-10 دقائق
• الدفع آمن 100٪ عبر تليجرام

📞 *الدعم الفني:*
للمساعدة تواصل مع: @YourSupportUsername
    """
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=reply_markup)


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة للقائمة الرئيسية"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🛒 شراء نجوم فري فاير", callback_data="buy")],
        [InlineKeyboardButton("📦 طلباتي", callback_data="my_orders")],
        [InlineKeyboardButton("ℹ️ المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎮 *القائمة الرئيسية*\n\nاختر ما تريد:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


# ============= تشغيل البوت =============
def main():
    """تشغيل البوت"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_packages, pattern="^buy$"))
    application.add_handler(CallbackQueryHandler(process_package_selection, pattern="^package_"))
    application.add_handler(CallbackQueryHandler(show_my_orders, pattern="^my_orders$"))
    application.add_handler(CallbackQueryHandler(show_help, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_freefire_id))
    
    print("🤖 البوت يعمل الآن...")
    application.run_polling()


if __name__ == "__main__":
    main()
