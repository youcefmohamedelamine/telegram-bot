import logging
from telegram import Update, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ضع توكن البوت الخاص بك
BOT_TOKEN = "ضع_التوكن_هنا"

# ضع رقم تيلغرام الخاص بك (المالك) حتى يصلك الطلب
OWNER_ID = 5825048491  

# بيانات الدفع (Telegram Stars)
PROVIDER_TOKEN = ""  # اتركه فارغ للدفع عبر Telegram Stars

# تفعيل الـ Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# الحالات
ASK_ID = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلا 👋\nاكتب /buy لشراء 100 لايك Free Fire مقابل 1000 نجمة.")


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("من فضلك أرسل لي الآن ID حسابك في Free Fire 📱")
    return ASK_ID


async def ask_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ff_id = update.message.text
    context.user_data["ff_id"] = ff_id

    # طلب الدفع
    title = "شراء 100 لايك Free Fire"
    description = f"ID: {ff_id}\nالسعر: 1000 نجمة"
    payload = "freefire_like"
    currency = "XTR"  # عملة نجوم تيليجرام
    prices = [LabeledPrice("100 لايك Free Fire", 1000)]  # 1000 نجمة

    await update.message.reply_invoice(
        title=title,
        description=description,
        payload=payload,
        provider_token=PROVIDER_TOKEN,
        currency=currency,
        prices=prices,
        start_parameter="freefire-stars",
    )
    return ConversationHandler.END


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    ff_id = context.user_data.get("ff_id", "غير معروف")

    # إشعار للمستخدم
    await update.message.reply_text("✅ تم الدفع بنجاح! سيتم تنفيذ طلبك خلال 24 ساعة.")

    # إشعار للمالك
    text = f"""
📢 طلب جديد:
- اسم المستخدم: @{user.username}
- ID Telegram: {user.id}
- ID Free Fire: {ff_id}
- الكمية: 100 لايك
- تم الدفع: 1000 نجمة
"""
    await context.bot.send_message(chat_id=OWNER_ID, text=text)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("buy", buy)],
        states={ASK_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_id)]},
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.PRE_CHECKOUT_QUERY, precheckout_callback))

    app.run_polling()


if __name__ == "__main__":
    main()
