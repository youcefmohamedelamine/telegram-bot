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
# CLEAN FILES - القوة في البساطة!
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
    user = update.effective_user
    save_user(user.id, user.username)
    
    keyboard = [
        [InlineKeyboardButton(f"📦 Complete Bundle - ⭐{STAR_PRICE * 10} (10 Files)", callback_data="get_all")],
        [InlineKeyboardButton("📂 Browse Templates", callback_data="show_files")],
        [InlineKeyboardButton("ℹ️ Why Clean Templates?", callback_data="why_clean")],
    ]
    
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])
    
    await update.message.reply_text(
        f"🎯 **Clean Code Templates**\n\n"
        f"✨ **Why programmers love clean templates:**\n"
        f"• 🚫 Zero bloat - No unnecessary code\n"
        f"• ⚡ Fast start - Jump right into coding\n"
        f"• 🎨 Full control - Your project, your way\n"
        f"• 📝 Professional structure - Industry standard\n"
        f"• 💎 Perfect blank canvas - Pure potential\n\n"
        f"🐍 Python • 💛 JavaScript • ☕ Java\n"
        f"⚡ C++ • 🔷 C# • 🐘 PHP\n"
        f"🌐 HTML • 🎨 CSS • 🔵 Go • 🦀 Rust\n\n"
        f"💰 **⭐{STAR_PRICE} per template** | Bundle: ⭐{STAR_PRICE * 10}\n\n"
        f"🎁 *\"Less is more\" - Start clean, build big!*",
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
    elif query.data == "why_clean":
        await explain_clean(query)
    elif query.data == "admin":
        await show_admin(query)
    elif query.data == "back":
        await back_menu(query)
    elif query.data.startswith("file_"):
        lang = query.data.replace("file_", "")
        await send_file_invoice(query, context, lang)

async def send_all_invoice(query, context):
    try:
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="📦 Complete Clean Templates Bundle",
            description="All 10 professionally structured blank templates. Zero bloat, maximum potential!",
            payload=f"all_{query.from_user.id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Complete Bundle", STAR_PRICE * 10)]
        )
        await query.message.edit_text(
            "💳 **Invoice sent!**\n\n"
            "You'll receive all 10 clean templates in a ZIP file.\n"
            "Perfect for starting multiple projects! 🚀"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.edit_text("❌ Error creating invoice. Contact support.")

async def show_file_list(query):
    keyboard = []
    for lang, info in FILES.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{info['emoji']} {info['desc']} - ⭐{STAR_PRICE}",
                callback_data=f"file_{lang}"
            )
        ])
    keyboard.append([InlineKeyboardButton("« Back to Menu", callback_data="back")])
    
    await query.message.edit_text(
        "📂 **Choose Your Clean Template:**\n\n"
        "Each template is:\n"
        "✨ Professionally structured\n"
        "🚫 100% bloat-free\n"
        "⚡ Ready to use instantly\n"
        "💎 Perfect blank canvas\n\n"
        f"💰 Only ⭐{STAR_PRICE} stars each!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_file_invoice(query, context, lang):
    if lang not in FILES:
        return
    
    file = FILES[lang]
    try:
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=f"{file['emoji']} {file['desc']}",
            description="Clean, professional template. Zero bloat. Full potential.",
            payload=f"file_{lang}_{query.from_user.id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(file['desc'], STAR_PRICE)]
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text("❌ Error creating invoice.")

async def explain_clean(query):
    await query.message.edit_text(
        "🎯 **Why Clean Templates Are Better:**\n\n"
        "**Traditional templates:**\n"
        "❌ Full of example code you'll delete\n"
        "❌ Bloated with unused features\n"
        "❌ Waste time removing stuff\n"
        "❌ Confusing for beginners\n\n"
        "**Our clean templates:**\n"
        "✅ **100% empty and clean**\n"
        "✅ **Professional structure only**\n"
        "✅ **Start coding immediately**\n"
        "✅ **Your code, your rules**\n"
        "✅ **No distractions**\n\n"
        "💡 *\"The best code is code you write yourself!\"*\n\n"
        "🎨 Think of it as a blank canvas for artists.\n"
        "That's what these templates are for coders!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Back to Menu", callback_data="back")
        ]])
    )

async def show_admin(query):
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Access denied!", show_alert=True)
        return
    
    if Session:
        try:
            session = Session()
            total_users = session.query(User).count()
            total_purchases = session.query(Purchase).count()
            total_revenue = session.query(Purchase).with_entities(
                Purchase.stars_paid
            ).all()
            revenue_sum = sum([p[0] for p in total_revenue]) if total_revenue else 0
            session.close()
            
            await query.message.edit_text(
                f"👑 **Admin Dashboard**\n\n"
                f"👥 Total Users: {total_users}\n"
                f"🛒 Total Sales: {total_purchases}\n"
                f"💰 Revenue: ⭐{revenue_sum} stars\n"
                f"📊 Avg per sale: ⭐{revenue_sum//total_purchases if total_purchases > 0 else 0}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Back", callback_data="back")
                ]])
            )
        except Exception as e:
            await query.message.edit_text(f"Error: {e}")

async def back_menu(query):
    keyboard = [
        [InlineKeyboardButton(f"📦 Complete Bundle - ⭐{STAR_PRICE * 10}", callback_data="get_all")],
        [InlineKeyboardButton("📂 Browse Templates", callback_data="show_files")],
        [InlineKeyboardButton("ℹ️ Why Clean Templates?", callback_data="why_clean")],
    ]
    
    if query.from_user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])
    
    await query.message.edit_text(
        f"🎯 **Clean Code Templates**\n\n"
        f"The power of simplicity!\n\n"
        f"💰 ⭐{STAR_PRICE} per template | Bundle: ⭐{STAR_PRICE * 10}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
            # Send ZIP with all files
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                for f in FILES.values():
                    zf.writestr(f['name'], f['content'])
                # Add README
                readme = """🎯 CLEAN CODE TEMPLATES
                
✨ Congratulations! You now have 10 professional blank templates.

🚫 NO BLOAT - Pure, clean structure
⚡ FAST START - Jump right into coding
🎨 FULL CONTROL - Your project, your way

Each file is perfectly structured and ready for your code!

Happy coding! 🚀
"""
                zf.writestr("README.txt", readme)
            
            zip_buffer.seek(0)
            
            await context.bot.send_document(
                chat_id=user_id,
                document=zip_buffer,
                filename="clean_templates_bundle.zip",
                caption=(
                    "✅ **Payment Successful!**\n\n"
                    "📦 Your complete clean templates bundle!\n\n"
                    "🎨 10 perfectly structured templates\n"
                    "🚫 Zero bloat - Pure potential\n"
                    "⚡ Start building amazing projects now!\n\n"
                    "🎁 Thank you for choosing quality! 🚀"
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
                        f"✅ **Payment Successful!**\n\n"
                        f"{file['emoji']} Your clean {file['desc']} is ready!\n\n"
                        f"🚫 Zero bloat\n"
                        f"⚡ Professional structure\n"
                        f"🎨 Perfect blank canvas\n\n"
                        f"Start coding now! 🚀"
                    ),
                    parse_mode="Markdown"
                )
                
                save_purchase(user_id, file['name'], STAR_PRICE)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error. Contact support.")

# ============================================================================
# MAIN
# ============================================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    logger.info("🚀 Clean Code Templates Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
