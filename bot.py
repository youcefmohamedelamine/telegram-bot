import logging
import io
import zipfile
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters
from sqlalchemy import create_engine, Column, BigInteger, String, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

# ============================================================================
# CONFIG
# ============================================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/botdb")
STAR_PRICE = 10  # سعر بسيط للتجربة
ADMIN_IDS = [123456789]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE
# ============================================================================

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255))
    join_date = Column(DateTime, default=datetime.utcnow)
    total_purchases = Column(Integer, default=0)

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    file_name = Column(String(255))
    stars_paid = Column(Integer)
    purchase_date = Column(DateTime, default=datetime.utcnow)

# Database setup
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    logger.info("✅ Database connected")
except Exception as e:
    logger.error(f"❌ Database error: {e}")
    Session = None

def save_user(user_id, username):
    if Session is None:
        return
    try:
        session = Session()
        if not session.query(User).filter_by(user_id=user_id).first():
            session.add(User(user_id=user_id, username=username))
            session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Error saving user: {e}")

def save_purchase(user_id, file_name, stars):
    if Session is None:
        return
    try:
        session = Session()
        session.add(Purchase(user_id=user_id, file_name=file_name, stars_paid=stars))
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.total_purchases += 1
        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Error saving purchase: {e}")

# ============================================================================
# FILES
# ============================================================================

FILES = {
    "python": {
        "name": "main.py", 
        "content": "# Python File\ndef main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()", 
        "emoji": "🐍"
    },
    "javascript": {
        "name": "index.js", 
        "content": "// JavaScript File\nfunction main() {\n    console.log('Hello World');\n}\nmain();", 
        "emoji": "💛"
    },
    "java": {
        "name": "Main.java", 
        "content": "// Java File\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello World\");\n    }\n}", 
        "emoji": "☕"
    },
    "cpp": {
        "name": "main.cpp", 
        "content": "// C++ File\n#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << \"Hello World\" << endl;\n    return 0;\n}", 
        "emoji": "⚡"
    },
    "html": {
        "name": "index.html", 
        "content": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Document</title>\n</head>\n<body>\n    <h1>Hello World</h1>\n</body>\n</html>", 
        "emoji": "🌐"
    },
}

# ============================================================================
# HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username)
    
    keyboard = [
        [InlineKeyboardButton(f"📦 All Files - ⭐{STAR_PRICE * len(FILES)}", callback_data="get_all")],
        [InlineKeyboardButton("📂 Choose File", callback_data="show_files")],
    ]
    
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin")])
    
    file_list = "\n".join([f"{f['emoji']} {f['name']}" for f in FILES.values()])
    
    await update.message.reply_text(
        f"👋 *Welcome {user.first_name}!*\n\n"
        f"📁 *Available Files:*\n{file_list}\n\n"
        f"💰 *Price:* ⭐{STAR_PRICE} per file\n\n"
        "Choose an option:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_all":
        await send_all_invoice(query, context)
    elif query.data == "show_files":
        await show_file_list(query)
    elif query.data == "admin":
        await show_admin(query)
    elif query.data == "back":
        await back_menu(query)
    elif query.data.startswith("file_"):
        lang = query.data.replace("file_", "")
        await send_file_invoice(query, context, lang)

async def send_all_invoice(query, context):
    """إرسال فاتورة لكل الملفات"""
    try:
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="📦 All Programming Files",
            description="Get all programming template files in one package!",
            payload=f"all_files_{query.from_user.id}",
            provider_token="",  # فارغ لـ Telegram Stars
            currency="XTR",
            prices=[LabeledPrice("All Files", STAR_PRICE * len(FILES))]
        )
        await query.message.edit_text("💳 Invoice sent! Complete payment to receive files.")
        logger.info(f"Invoice sent to {query.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        await query.message.edit_text(f"❌ Error: {str(e)}\n\nMake sure bot can send invoices.")

async def show_file_list(query):
    keyboard = []
    for lang, info in FILES.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{info['emoji']} {info['name']} - ⭐{STAR_PRICE}", 
                callback_data=f"file_{lang}"
            )
        ])
    keyboard.append([InlineKeyboardButton("« Back", callback_data="back")])
    
    await query.message.edit_text(
        f"📂 *Choose a file:*\n\n💰 Each file costs ⭐{STAR_PRICE}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_file_invoice(query, context, lang):
    """إرسال فاتورة لملف واحد"""
    if lang not in FILES:
        await query.answer("❌ File not found!")
        return
    
    file = FILES[lang]
    try:
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=f"{file['emoji']} {file['name']}",
            description=f"Programming template file",
            payload=f"file_{lang}_{query.from_user.id}",
            provider_token="",  # فارغ لـ Telegram Stars
            currency="XTR",
            prices=[LabeledPrice(file['name'], STAR_PRICE)]
        )
        logger.info(f"Invoice sent to {query.from_user.id} for {file['name']}")
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text(f"❌ Error: {str(e)}")

async def show_admin(query):
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Access denied!", show_alert=True)
        return
    
    if Session:
        try:
            session = Session()
            total_users = session.query(User).count()
            total_purchases = session.query(Purchase).count()
            session.close()
            
            await query.message.edit_text(
                f"👑 *Admin Panel*\n\n"
                f"👥 Users: {total_users}\n"
                f"🛒 Purchases: {total_purchases}",
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.message.edit_text(f"Error: {e}")
    else:
        await query.message.edit_text("Database not connected")

async def back_menu(query):
    keyboard = [
        [InlineKeyboardButton(f"📦 All Files - ⭐{STAR_PRICE * len(FILES)}", callback_data="get_all")],
        [InlineKeyboardButton("📂 Choose File", callback_data="show_files")],
    ]
    
    if query.from_user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin")])
    
    await query.message.edit_text(
        "👋 *Welcome!*\n\nChoose an option:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================================
# PAYMENT HANDLERS
# ============================================================================

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الموافقة على الدفع"""
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"Payment approved for user {query.from_user.id}")

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال الملفات بعد الدفع الناجح"""
    payment = update.message.successful_payment
    user_id = update.effective_user.id
    payload = payment.invoice_payload
    
    logger.info(f"Payment received from {user_id}: {payload}")
    
    try:
        if "all_files" in payload:
            # إرسال كل الملفات كـ ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                for f in FILES.values():
                    zf.writestr(f['name'], f['content'])
            zip_buffer.seek(0)
            
            await context.bot.send_document(
                chat_id=user_id,
                document=zip_buffer,
                filename="programming_files.zip",
                caption="✅ *Payment Successful!*\n\n📦 All files delivered!\n\nThank you! 🎉",
                parse_mode="Markdown"
            )
            
            save_purchase(user_id, "all_files.zip", STAR_PRICE * len(FILES))
            
        elif payload.startswith("file_"):
            # إرسال ملف واحد
            lang = payload.split("_")[1]
            if lang in FILES:
                file = FILES[lang]
                file_buffer = io.BytesIO(file['content'].encode('utf-8'))
                
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file_buffer,
                    filename=file['name'],
                    caption=f"✅ *Payment Successful!*\n\n{file['emoji']} {file['name']} delivered!\n\nThank you! 🎉",
                    parse_mode="Markdown"
                )
                
                save_purchase(user_id, file['name'], STAR_PRICE)
        
        await update.message.reply_text(
            "🎉 Thank you!\n\nType /start to get more files!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error delivering files: {e}")
        await update.message.reply_text("❌ Error delivering files. Contact support.")

# ============================================================================
# MAIN
# ============================================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    logger.info("🚀 Bot started with Telegram Stars payment!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
