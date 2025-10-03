import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler


# 🔑 ضع التوكن هنا
BOT_TOKEN2 = "ضع_توكن_البوت_هنا"

# 🧑‍💻 ضع رقم معرف المالك (Telegram ID)
OWNER_ID2 = 5825048491   # مثال فقط غيره بمعرفك الحقيقي

# إعداد اللوغ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# دالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name

    keyboard = [
        [InlineKeyboardButton("🌀 شراء لا شيء", callback_data="buy_nothing")],
        [InlineKeyboardButton("ℹ️ لماذا؟", callback_data="why")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"""
👋 أهلاً <b>{name}</b>  
مرحباً بك في بوت <b>بيع اللاشيء</b> ✨  

هنا يمكنك شراء "لا شيء" لأنك تملك كل شيء بالفعل 🌌  

اختر من الأسفل:
    """

    await update.message.reply_html(text, reply_markup=reply_markup)


# الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    await query.answer()

    if query.data == "buy_nothing":
        msg = f"✅ تهانينا {user.first_name}! لقد اشتريت <b>لا شيء</b> 🎉\n\nلكن في الحقيقة، أنت أصلاً تملك كل شيء 💫"
        await query.edit_message_text(msg, parse_mode="HTML")

        # إشعار للمالك
        try:
            await context.bot.send_message(
                chat_id=OWNER_ID2,
                text=f"📢 المستخدم {user.first_name} (@{user.username}) اشترى (لا شيء)!"
            )
        except:
            pass

    elif query.data == "why":
        await query.edit_message_text("🌌 هذا البوت فلسفي 😅\n\nنبيعك (لا شيء) لتتذكر أنك غني بما لديك.")


def main():
    app = Application.builder().token(BOT_TOKEN2).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("✅ بوت بيع اللاشيء شغال...")
    app.run_polling()


if __name__ == "__main__":
    main()
