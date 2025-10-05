import telebot
from telebot import types
# تأكد من أن ملف config.py يحتوي على TOKEN و STAR_PROVIDER_TOKEN
from config import TOKEN, STAR_PROVIDER_TOKEN 
# استيراد الوظائف الجديدة (PostgreSQL)
from database import setup_db, save_payment 
import os
import asyncio # نحتاج إلى asyncio لتشغيل دالة setup_db

# ----------------------------------
# 1. إعداد البوت
# ----------------------------------
bot = telebot.TeleBot(TOKEN)

# تهيئة قاعدة البيانات لمرة واحدة قبل بدء البوت
# نستخدم asyncio.run لتشغيل دالة async مرة واحدة.
print("⏳ جاري تهيئة قاعدة بيانات PostgreSQL...")
try:
    asyncio.run(setup_db())
    print("✅ تم ربط قاعدة البيانات بنجاح.")
except Exception as e:
    print(f"❌ فشل ربط قاعدة البيانات: {e}")
    # إذا فشل الاتصال بالقاعدة، يجب أن يتوقف البوت
    # exit()

# ----------------------------------
# 2. الدوال المساعدة
# ----------------------------------

# وظيفة لإنشاء زر الدفع (Pay Button)
def payment_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    # يجب أن يكون الزر pay=True في الفاتورة نفسها وليس هنا (هنا لإرسال الفاتورة)
    # هذا الزر يتم استخدامه فقط إذا كنت لا تستخدم WebApp.
    # بما أننا نستخدم send_invoice، نكتفي بالزر الذي يُنشئه Telegram تلقائيًا.
    return keyboard 

# وظيفة لإنشاء زر "شراء صورة"
def start_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="🛒 شراء صورة (1 ⭐)", callback_data="buy_image")
    keyboard.add(button)
    return keyboard

# ----------------------------------
# 3. معالجات الرسائل
# ----------------------------------

# معالج أمر /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(
        message.chat.id,
        "أهلاً بك! اضغط الزر أدناه لشراء الصورة بنجمة تيليجرام واحدة (XTR).",
        reply_markup=start_keyboard()
    )

# معالج الضغط على زر "شراء صورة"
@bot.callback_query_handler(func=lambda call: call.data == "buy_image")
def handle_buy_image(call):
    # التأكد من وجود رمز الموفر
    if not STAR_PROVIDER_TOKEN:
        bot.send_message(call.message.chat.id, "❌ رمز موفر الدفع غير مُعدّ. تواصل مع المطور.")
        return
        
    prices = [types.LabeledPrice(label="نجمة تيليجرام واحدة", amount=1000)] # 1 XTR = 1000 وحدة
    
    bot.send_invoice(
        call.message.chat.id,
        title="شراء الصورة",
        description="صورة مميزة مقابل نجمة تيليجرام واحدة (XTR)!",
        invoice_payload=f"image_purchase_{call.from_user.id}",
        # استخدم رمز الموفر المُخزّن في config
        provider_token=STAR_PROVIDER_TOKEN, 
        currency="XTR", # العملة هي نجوم تيليجرام
        prices=prices,
        # لا نضع reply_markup هنا، نترك تيليجرام يُنشئ زر الدفع التلقائي
        # reply_markup=payment_keyboard() 
    )

# معالج التحقق المسبق من الدفع
@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout_query(pre_checkout_query):
    # لا تحتاج إلى تحققات إضافية لنجوم تيليجرام عادةً
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# معالج الدفع الناجح
@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    user_id = message.from_user.id
    # استخدم transaction_id كمعرف دفع فريد
    payment_id = message.successful_payment.telegram_payment_charge_id
    amount = message.successful_payment.total_amount
    currency = message.successful_payment.currency

    # 1. إرسال رسالة التأكيد
    bot.send_message(message.chat.id, "✅ تم قبول الدفع، يرجى الانتظار لتلقي الصورة! 🥳")
    
    # 2. حفظ معلومات الدفع في قاعدة البيانات (غير متزامن - سنستخدم asyncio.run مؤقتًا)
    try:
        # بما أن save_payment أصبحت async، يجب تشغيلها بهذه الطريقة في كود متزامن
        asyncio.run(save_payment(user_id, payment_id, amount, currency))
    except Exception as e:
        print(f"❌ خطأ في حفظ الدفع في قاعدة البيانات: {e}")

    # 3. إرسال الصورة
    photo_path = 'img/img-X9ptcIuiOMICY0BUQukCpVYS.png'
    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="🥳شكراً لك على الشراء!🤗")
    else:
        bot.send_message(message.chat.id, "عذراً، الصورة غير موجودة على الخادم.")

# معالج أمر /paysupport
@bot.message_handler(commands=['paysupport'])
def handle_pay_support(message):
    bot.send_message(
        message.chat.id,
        "شراء الصور لا يتضمن استرداداً للمبالغ المدفوعة. "
        "إذا كانت لديك أية استفسارات، يرجى التواصل مع الدعم الفني."
    )

# ----------------------------------
# 4. تشغيل البوت (Polling)
# ----------------------------------
# إذا كنت تستخدم Railway، يجب عليك استخدام الـ Webhook بدلاً من Polling.
# لكن إذا كنت مصرًا على Polling، يمكن أن يعمل لفترة وجيزة.
#bot.polling()
