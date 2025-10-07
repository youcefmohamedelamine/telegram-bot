import logging
import io
import zipfile
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters
from sqlalchemy import create_engine, Column, BigInteger, String, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

# ============================================================================
# CONFIG
# ============================================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/botdb")
STAR_PRICE = 999
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
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base.metadata.create_all(engine)
Session = scoped_session(sessionmaker(bind=engine))

def get_db():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

# ============================================================================
# FILES
# ============================================================================

FILES = {
    "python": {"name": "main.py", "content": "# Python\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()", "emoji": "🐍"},
    "javascript": {"name": "index.js", "content": "// JavaScript\nfunction main() {\n    // code\n}\nmain();", "emoji": "💛"},
    "java": {"name": "Main.java", "content": "// Java\npublic class Main {\n    public static void main(String[] args) {\n    }\n}", "emoji": "☕"},
    "cpp": {"name": "main.cpp", "content": "// C++\n#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}", "emoji": "⚡"},
    "html": {"name": "index.html", "content": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Document</title>\n</head>\n<body>\n</body>\n</html>", "emoji": "🌐"},
}

# ============================================================================
# HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Save user
    session = next(get_db())
    if not session.query(User).filter_by(user_id=user.id).first():
        session.add(User(user_id=user.id, username=user.username))
        session.commit()
    
    keyboard = [
        [InlineKeyboardButton(f"📦 All Files (ZIP) - ⭐{STAR_PRICE*5}", callback_data="get_all")],
        [InlineKeyboardButton("📂 Choose File", callback_data="show_files")],
    ]
    
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin")])
    
    await update.message.reply_text(
        f"👋 *Welcome {user.first_name}!*\n\n"
        f"💰 Price: ⭐{STAR_PRICE} per file\n"
        "Choose an option:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_all":
        await send_all_files(query, context)
    elif query.data == "show_files":
        await show_file_list(query, context)
    elif query.data == "admin":
        await show_admin(query)
    elif query.data == "back":
        await back_menu(query)
    elif query.data.startswith("file_"):
        lang = query.data.replace("file_", "")
        await send_single_file(query, context, lang)

async def send_all_files(query, context):
    await query.message.edit_text("⏳ Creating ZIP...")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for f in FILES.values():
            zf.writestr(f['name'], f['content'])
    zip_buffer.seek(0)
    
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title="📦 All Files Package",
        description="Get all programming files in ZIP",
        payload=f"zip_{query.from_user.id}",
        currency="XTR",
        prices=[{"label": "All Files", "amount": STAR_PRICE * 5}]
    )

async def show_file_list(query, context):
    keyboard = []
    for lang, info in FILES.items():
        keyboard.append([InlineKeyboardButton(f"{info['emoji']} {info['name']} - ⭐{STAR_PRICE}", callback_data=f"file_{lang}")])
    keyboard.append([InlineKeyboardButton("« Back", callback_data="back")])
    
    await query.message.edit_text("📂 *Choose a file:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_single_file(query, context, lang):
    if lang not in FILES:
        return
    
    file = FILES[lang]
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=f"{file['emoji']} {file['name']}",
        description=f"Template file",
        payload=f"file_{lang}_{query.from_user.id}",
        currency="XTR",
        prices=[{"label": file['name'], "amount": STAR_PRICE}]
    )

async def show_admin(query):
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Access denied!", show_alert=True)
        return
    
    session = next(get_db())
    total_users = session.query(User).count()
    total_purchases = session.query(Purchase).count()
    
    await query.message.edit_text(
        f"👑 *Admin Panel*\n\n"
        f"👥 Users: {total_users}\n"
        f"🛒 Purchases: {total_purchases}",
        parse_mode="Markdown"
    )

async def back_menu(query):
    keyboard = [
        [InlineKeyboardButton(f"📦 All Files - ⭐{STAR_PRICE*5}", callback_data="get_all")],
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
# PAYMENT
# ============================================================================

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    user_id = update.effective_user.id
    payload = payment.invoice_payload
    
    # Save purchase
    session = next(get_db())
    
    if payload.startswith("zip_"):
        # Send ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for f in FILES.values():
                zf.writestr(f['name'], f['content'])
        zip_buffer.seek(0)
        
        await context.bot.send_document(
            chat_id=user_id,
            document=zip_buffer,
            filename="files.zip",
            caption="✅ *Payment Successful!*\n📦 All files delivered!",
            parse_mode="Markdown"
        )
        
        session.add(Purchase(user_id=user_id, file_name="files.zip", stars_paid=STAR_PRICE*5))
        
    elif payload.startswith("file_"):
        # Send single file
        lang = payload.split("_")[1]
        if lang in FILES:
            file = FILES[lang]
            file_buffer = io.BytesIO(file['content'].encode('utf-8'))
            
            await context.bot.send_document(
                chat_id=user_id,
                document=file_buffer,
                filename=file['name'],
                caption=f"✅ *Payment Successful!*\n{file['emoji']} File delivered!",
                parse_mode="Markdown"
            )
            
            session.add(Purchase(user_id=user_id, file_name=file['name'], stars_paid=STAR_PRICE))
    
    # Update user stats
    user = session.query(User).filter_by(user_id=user_id).first()
    if user:
        user.total_purchases += 1
    
    session.commit()

# ============================================================================
# MAIN
# ============================================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    logger.info("🚀 Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
