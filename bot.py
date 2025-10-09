import logging
import io
import zipfile
import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters
from sqlalchemy import create_engine, Column, BigInteger, String, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

# ============================================================================
# CONFIG
# ============================================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/botdb")
# رابط موقعك على GitHub Pages (غيّر هذا للرابط الصحيح)
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-username.github.io/your-repo")
STAR_PRICE = 999

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
    except:
        pass

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
    except:
        pass

# ============================================================================
# CLEAN FILES
# ============================================================================

FILES = {
    "python": {
        "name": "main.py",
        "content": """# Python Clean Template
# Zero bloat. Pure simplicity.
# Start your project the right way.

def main():
    pass

if __name__ == "__main__":
    main()
""",
        "emoji": "🐍",
        "desc": "Clean Python Template"
    },
    "javascript": {
        "name": "index.js",
        "content": """// JavaScript Clean Template
// No frameworks. No dependencies. Just code.
// Perfect blank canvas for your project.

function main() {
    // Your code here
}

main();
""",
        "emoji": "💛",
        "desc": "Clean JavaScript Template"
    },
    "java": {
        "name": "Main.java",
        "content": """// Java Clean Template
// Enterprise-ready blank structure
// Professional starting point

public class Main {
    public static void main(String[] args) {
        // Your code here
    }
}
""",
        "emoji": "☕",
        "desc": "Clean Java Template"
    },
    "cpp": {
        "name": "main.cpp",
        "content": """// C++ Clean Template
// Optimized structure. Zero overhead.
// Performance-first approach.

#include <iostream>
using namespace std;

int main() {
    // Your code here
    return 0;
}
""",
        "emoji": "⚡",
        "desc": "Clean C++ Template"
    },
    "csharp": {
        "name": "Program.cs",
        "content": """// C# Clean Template
// .NET ready structure
// Professional blank slate

using System;

class Program
{
    static void Main(string[] args)
    {
        // Your code here
    }
}
""",
        "emoji": "🔷",
        "desc": "Clean C# Template"
    },
    "php": {
        "name": "index.php",
        "content": """<?php
// PHP Clean Template
// Web-ready blank structure
// No bloat. Just potential.

function main() {
    // Your code here
}

main();
?>
""",
        "emoji": "🐘",
        "desc": "Clean PHP Template"
    },
    "html": {
        "name": "index.html",
        "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clean HTML Template</title>
    <!-- Pure HTML. No frameworks. Full control. -->
</head>
<body>
    <!-- Your content here -->
</body>
</html>
""",
        "emoji": "🌐",
        "desc": "Clean HTML Template"
    },
    "css": {
        "name": "style.css",
        "content": """/* CSS Clean Template */
/* Zero bloat. Pure styling potential. */
/* Build your design from scratch. */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Your styles here */
""",
        "emoji": "🎨",
        "desc": "Clean CSS Template"
    },
    "go": {
        "name": "main.go",
        "content": """// Go Clean Template
// Minimal structure. Maximum efficiency.
// Google's simplicity philosophy.

package main

import "fmt"

func main() {
    // Your code here
    fmt.Println("Ready to code!")
}
""",
        "emoji": "🔵",
        "desc": "Clean Go Template"
    },
    "rust": {
        "name": "main.rs",
        "content": """// Rust Clean Template
// Memory-safe blank slate
// Zero-cost abstraction ready

fn main() {
    // Your code here
    println!("Ready to build!");
}
""",
        "emoji": "🦀",
        "desc": "Clean Rust Template"
    }
}

# ============================================================================
# HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة البداية مع زر فتح التطبيق فقط"""
    user = update.effective_user
    save_user(user.id, user.username)
    
    keyboard = [
        [InlineKeyboardButton("🚀 فتح المتجر", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    
    await update.message.reply_text(
        f"🎯 **مرحباً {user.first_name}!**\n\n"
        f"✨ **Clean Code Templates**\n\n"
        f"🐍 Python • 💛 JavaScript • ☕ Java\n"
        f"⚡ C++ • 🔷 C# • 🐘 PHP\n"
        f"🌐 HTML • 🎨 CSS • 🔵 Go • 🦀 Rust\n\n"
        f"💰 **⭐{STAR_PRICE} نجمة للقالب الواحد**\n"
        f"📦 **⭐{STAR_PRICE * 10} نجمة للحزمة الكاملة**\n\n"
        f"اضغط الزر أدناه لفتح المتجر 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة البيانات المرسلة من Web App"""
    try:
        data = json.loads(update.message.web_app_data.data)
        logger.info(f"Received web app data: {data}")
        
        user_id = update.effective_user.id
        
        if data.get('action') == 'purchase':
            if data.get('type') == 'bundle':
                # إرسال فاتورة الحزمة
                await context.bot.send_invoice(
                    chat_id=user_id,
                    title="📦 Complete Clean Templates Bundle",
                    description="All 10 professionally structured blank templates. Zero bloat, maximum potential!",
                    payload=f"all_{user_id}",
                    provider_token="",
                    currency="XTR",
                    prices=[LabeledPrice("Complete Bundle", STAR_PRICE * 10)]
                )
            elif data.get('type') == 'single':
                lang = data.get('item')
                if lang and lang in FILES:
                    file = FILES[lang]
                    # إرسال فاتورة قالب واحد
                    await context.bot.send_invoice(
                        chat_id=user_id,
                        title=f"{file['emoji']} {file['desc']}",
                        description="Clean, professional template. Zero bloat. Full potential.",
                        payload=f"file_{lang}_{user_id}",
                        provider_token="",
                        currency="XTR",
                        prices=[LabeledPrice(file['desc'], STAR_PRICE)]
                    )
    except Exception as e:
        logger.error(f"Error handling web app data: {e}")
        await update.message.reply_text("❌ حدث خطأ. حاول مرة أخرى.")

# ============================================================================
# PAYMENT
# ============================================================================

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    user_id = update.effective_user.id
    payload = payment.invoice_payload
    
    try:
        if "all_" in payload:
            # إرسال ZIP مع جميع الملفات
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                for f in FILES.values():
                    zf.writestr(f['name'], f['content'])
                # إضافة README
                readme = """🎯 CLEAN CODE TEMPLATES

✨ تهانينا! لديك الآن 10 قوالب احترافية نظيفة.

🚫 بدون زوائد - هيكلة نظيفة تماماً
⚡ بداية سريعة - ابدأ البرمجة فوراً
🎨 تحكم كامل - مشروعك بطريقتك

كل ملف مهيكل بشكل مثالي وجاهز لكودك!

برمجة سعيدة! 🚀
"""
                zf.writestr("README.txt", readme)
            
            zip_buffer.seek(0)
            
            await context.bot.send_document(
                chat_id=user_id,
                document=zip_buffer,
                filename="clean_templates_bundle.zip",
                caption=(
                    "✅ **تم الدفع بنجاح!**\n\n"
                    "📦 حزمة القوالب النظيفة الكاملة!\n\n"
                    "🎨 10 قوالب مهيكلة بشكل مثالي\n"
                    "🚫 بدون زوائد - إمكانيات نقية\n"
                    "⚡ ابدأ ببناء مشاريع رائعة الآن!\n\n"
                    "🎁 شكراً لاختيارك الجودة! 🚀"
                ),
                parse_mode="Markdown"
            )
            
            save_purchase(user_id, "bundle.zip", STAR_PRICE * 10)
            
        elif "file_" in payload:
            lang = payload.split("_")[1]
            if lang in FILES:
                file = FILES[lang]
                file_buffer = io.BytesIO(file['content'].encode('utf-8'))
                
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file_buffer,
                    filename=file['name'],
                    caption=(
                        f"✅ **تم الدفع بنجاح!**\n\n"
                        f"{file['emoji']} قالب {file['desc']} جاهز!\n\n"
                        f"🚫 بدون زوائد\n"
                        f"⚡ هيكلة احترافية\n"
                        f"🎨 لوحة فارغة مثالية\n\n"
                        f"ابدأ البرمجة الآن! 🚀"
                    ),
                    parse_mode="Markdown"
                )
                
                save_purchase(user_id, file['name'], STAR_PRICE)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ خطأ. تواصل مع الدعم.")

# ============================================================================
# MAIN
# ============================================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    
    # Web App data handler
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    
    # Payment handlers
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    logger.info("🚀 Clean Code Templates Bot started!")
    logger.info(f"📱 Web App URL: {WEB_APP_URL}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
