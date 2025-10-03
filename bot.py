# file: bot_pay_stars.py
import os
import logging

from telegram import LabeledPrice, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    PreCheckoutQueryHandler,
)


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")  # اضف المتغير في Railway/Env
# مثال: 100 stars (افتراض: 1 star = 1 وحدة في smallest unit)
PRICE_STARS = 100

# رسالة المنتج (ما تبيعه)
PRODUCT_TITLE = "رسالة خاصة"
PRODUCT_DESCRIPTION = "أرسل رسالة 'أحبك' إلى من تختار — مقابل 100 نجمة (Stars)."
START_PARAM = "buy_love_message_v1"  # أي string فريد

# ---------- الأمر /start (اختياري) ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً! استخدم /buy لإرسال رسالة مقابل نجوم.\n"
        "مثال: /buy  -> يرسل الرسالة لك بعد الدفع\n"
        "أو: /buy @username  -> يرسل الرسالة ليوزر آخر"
    )

# ---------- أمر /buy (يرسل الفاتورة) ----------
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # إن أردت إرسال لاحقًا ليوزر آخر، خزن هدف الإرسال داخل payload (مثال مبسط)
    target = None
    if context.args:
        target = context.args[0]  # مثل '@username' أو user_id
    payload = f"buy_message|{chat_id}|{target or ''}"

    prices = [LabeledPrice(label="رسالة 'أحبك'", amount=PRICE_STARS)]
    # provider_token يجب أن يُحذف / يُترك فارغ للـ XTR — مكتوب في التوثيق
    # بعض مكتبات تسمح بتمرير provider_token=""، وبعضها يتجاهل الحقل. سنمرره كـ "" هنا.
    try:
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=PRODUCT_TITLE,
            description=PRODUCT_DESCRIPTION,
            payload=payload,
            provider_token="",      # اتركه فارغًا للـ XTR
            currency="XTR",         # عملة النجوم
            prices=prices,
            start_parameter=START_PARAM,
        )
    except Exception as e:
        logger.exception("failed to send invoice")
        await update.message.reply_text("حصل خطأ أثناء إنشاء الفاتورة. حاول لاحقًا.")

# ---------- التعامل مع pre_checkout_query ----------
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    # هنا يمكنك فحص الـ payload أو التحقق من قواعدك ثم القبول
    try:
        await context.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
    except Exception as e:
        logger.exception("precheckout handling failed")

# ---------- معالجة successful_payment ----------
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    successful_payment = msg.successful_payment
    # احفظ سجل الدفع إن أردت: successful_payment.telegram_payment_charge_id
    logger.info("Received successful payment: %s", successful_payment.to_dict())

    # payload الذي أرسلناه في الفاتورة
    # مثال payload = "buy_message|<buyer_chat_id>|@target"
    payload = msg.invoice_payload or ""
    parts = payload.split("|")
    if len(parts) >= 3 and parts[0] == "buy_message":
        buyer_chat_id = int(parts[1]) if parts[1] else msg.from_user.id
        target = parts[2] or ""
    else:
        buyer_chat_id = msg.from_user.id
        target = ""

    # الرسالة التي نبيعها
    the_message_text = "أحبك ❤️"

    # إذا حُدِّد target كـ @username فحاول إرسال له، وإلا أعد الرسالة للمشتري
    if target.startswith("@"):
        try:
            await context.bot.send_message(chat_id=target, text=the_message_text, parse_mode=ParseMode.HTML)
            await msg.reply_text("تم إرسال الرسالة إلى " + target)
        except Exception as e:
            logger.exception("failed to send to target")
            # إن فشل الإرسال، أرسل للمشتري بدلًا من ذلك:
            await context.bot.send_message(chat_id=buyer_chat_id,
                                           text=f"لم نستطع إرسال الرسالة إلى {target}. تم إرسالها إليك بدلاً من ذلك:\n\n{the_message_text}")
    else:
        # إرسال للمشتري
        await context.bot.send_message(chat_id=buyer_chat_id, text=the_message_text)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    # pre-checkout
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    # successful payment updates: filter
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    logger.info("Bot started (payments example).")
    app.run_polling()


if __name__ == "__main__":
    main()
