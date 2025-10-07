"""
Telegram Bot - Professional Programming Files Bot with Database
- PostgreSQL Database Integration
- User Management System
- Purchase History Tracking
- Error Handling & Logging
- Statistics & Analytics
"""

import logging
import io
import zipfile
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters
from sqlalchemy import create_engine, Column, BigInteger, String, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

# ============================================================================
# CONFIG
# ============================================================================

BOT_TOKEN = "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/botdb")
STAR_PRICE = 999
ADMIN_IDS = [123456789]  # ضع معرف التيليجرام الخاص بك هنا

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE SETUP
# ============================================================================

Base = declarative_base()

class User(Base):
    """Users table"""
    __tablename__ = 'users'
    
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    join_date = Column(DateTime, default=datetime.utcnow)
    is_premium = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    total_purchases = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)

class Purchase(Base):
    """Purchases table"""
    __tablename__ = 'purchases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    stars_paid = Column(Integer, nullable=False)
    purchase_date = Column(DateTime, default=datetime.utcnow)
    transaction_id = Column(String(255), nullable=True)

class BotStats(Base):
    """Bot statistics table"""
    __tablename__ = 'bot_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    total_users = Column(Integer, default=0)
    total_purchases = Column(Integer, default=0)
    total_revenue = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

class ErrorLog(Base):
    """Error logs table"""
    __tablename__ = 'error_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    error_message = Column(Text, nullable=False)
    error_traceback = Column(Text, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow)

# Database engine and session
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    logger.info("✅ Database connected successfully")
except Exception as e:
    logger.error(f"❌ Database connection failed: {e}")
    Session = None

@contextmanager
def get_db():
    """Database session context manager"""
    if Session is None:
        yield None
        return
    
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def add_or_update_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Add or update user in database"""
    try:
        with get_db() as db:
            if db is None:
                return False
            
            user = db.query(User).filter_by(user_id=user_id).first()
            
            if user:
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.last_activity = datetime.utcnow()
            else:
                user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                db.add(user)
                update_bot_stats(db, new_user=True)
            
            return True
    except Exception as e:
        logger.error(f"Error adding/updating user: {e}")
        return False

def add_purchase(user_id: int, file_name: str, file_type: str, stars_paid: int, transaction_id: str = None):
    """Add purchase to database"""
    try:
        with get_db() as db:
            if db is None:
                return False
            
            purchase = Purchase(
                user_id=user_id,
                file_name=file_name,
                file_type=file_type,
                stars_paid=stars_paid,
                transaction_id=transaction_id
            )
            db.add(purchase)
            
            # Update user stats
            user = db.query(User).filter_by(user_id=user_id).first()
            if user:
                user.total_purchases += 1
                user.total_spent += stars_paid
            
            # Update bot stats
            update_bot_stats(db, new_purchase=True, revenue=stars_paid)
            
            return True
    except Exception as e:
        logger.error(f"Error adding purchase: {e}")
        return False

def update_bot_stats(db, new_user=False, new_purchase=False, revenue=0):
    """Update bot statistics"""
    try:
        stats = db.query(BotStats).first()
        if not stats:
            stats = BotStats()
            db.add(stats)
        
        if new_user:
            stats.total_users = db.query(User).count()
        if new_purchase:
            stats.total_purchases += 1
        if revenue:
            stats.total_revenue += revenue
        
        stats.last_updated = datetime.utcnow()
    except Exception as e:
        logger.error(f"Error updating stats: {e}")

def get_user_purchases(user_id: int):
    """Get user purchase history"""
    try:
        with get_db() as db:
            if db is None:
                return []
            return db.query(Purchase).filter_by(user_id=user_id).all()
    except Exception as e:
        logger.error(f"Error getting purchases: {e}")
        return []

def get_bot_stats():
    """Get bot statistics"""
    try:
        with get_db() as db:
            if db is None:
                return None
            stats = db.query(BotStats).first()
            if not stats:
                return {"total_users": 0, "total_purchases": 0, "total_revenue": 0}
            return {
                "total_users": stats.total_users,
                "total_purchases": stats.total_purchases,
                "total_revenue": stats.total_revenue
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return None

def log_error(user_id: int, error_msg: str, traceback: str = None):
    """Log error to database"""
    try:
        with get_db() as db:
            if db is None:
                return
            error_log = ErrorLog(
                user_id=user_id,
                error_message=error_msg,
                error_traceback=traceback
            )
            db.add(error_log)
    except Exception as e:
        logger.error(f"Error logging to database: {e}")

# ============================================================================
# FILES DATA
# ============================================================================

FILES = {
    "python": {
        "name": "main.py",
        "content": """# Python File
# Start coding here

def main():
    pass

if __name__ == "__main__":
    main()
""",
        "desc": "🐍 Python File",
        "emoji": "🐍"
    },
    "javascript": {
        "name": "index.js",
        "content": """// JavaScript File
// Start coding here

function main() {
    // Your code
}

main();
""",
        "desc": "💛 JavaScript File",
        "emoji": "💛"
    },
    "java": {
        "name": "Main.java",
        "content": """// Java File
// Start coding here

public class Main {
    public static void main(String[] args) {
        // Your code
    }
}
""",
        "desc": "☕ Java File",
        "emoji": "☕"
    },
    "cpp": {
        "name": "main.cpp",
        "content": """// C++ File
// Start coding here

#include <iostream>
using namespace std;

int main() {
    // Your code
    return 0;
}
""",
        "desc": "⚡ C++ File",
        "emoji": "⚡"
    },
    "csharp": {
        "name": "Program.cs",
        "content": """// C# File
// Start coding here

using System;

class Program
{
    static void Main(string[] args)
    {
        // Your code
    }
}
""",
        "desc": "🔷 C# File",
        "emoji": "🔷"
    },
    "php": {
        "name": "index.php",
        "content": """<?php
// PHP File
// Start coding here

function main() {
    // Your code
}

main();
?>
""",
        "desc": "🐘 PHP File",
        "emoji": "🐘"
    },
    "html": {
        "name": "index.html",
        "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    <!-- Your HTML here -->
</body>
</html>
""",
        "desc": "🌐 HTML File",
        "emoji": "🌐"
    },
    "css": {
        "name": "style.css",
        "content": """/* CSS File */
/* Start styling here */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
}
""",
        "desc": "🎨 CSS File",
        "emoji": "🎨"
    },
    "go": {
        "name": "main.go",
        "content": """// Go File
// Start coding here

package main

import "fmt"

func main() {
    // Your code
    fmt.Println("Hello, World!")
}
""",
        "desc": "🔵 Go File",
        "emoji": "🔵"
    },
    "rust": {
        "name": "main.rs",
        "content": """// Rust File
// Start coding here

fn main() {
    // Your code
    println!("Hello, World!");
}
""",
        "desc": "🦀 Rust File",
        "emoji": "🦀"
    }
}

# ============================================================================
# HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    try:
        user = update.effective_user
        add_or_update_user(user.id, user.username, user.first_name, user.last_name)
        
        keyboard = [
            [InlineKeyboardButton(f"📦 Get All Files (ZIP) - ⭐{STAR_PRICE*10}", callback_data="get_all")],
            [InlineKeyboardButton("📂 Choose Language", callback_data="show_files")],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about")]
        ]
        
        if user.id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])
        
        file_list = "\n".join([f"• {f['emoji']} {f['name']}" for f in FILES.values()])
        
        await update.message.reply_text(
            f"👋 *Welcome {user.first_name}!*\n\n"
            "I can send you empty template files in different languages.\n\n"
            f"📁 *Available Files:*\n{file_list}\n\n"
            f"💰 *Price:* ⭐{STAR_PRICE} stars per file\n\n"
            "Choose an option below:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"User {user.id} ({user.username}) started bot")
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    
    try:
        await query.answer()
        
        if query.data == "get_all":
            await send_all_files(query, context)
        elif query.data == "show_files":
            await show_file_list(query, context)
        elif query.data == "my_stats":
            await show_user_stats(query, context)
        elif query.data == "about":
            await show_about(query, context)
        elif query.data == "admin":
            await show_admin_panel(query, context)
        elif query.data == "back":
            await back_to_menu(query, context)
        elif query.data.startswith("file_"):
            lang = query.data.replace("file_", "")
            await send_single_file(query, context, lang)
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        log_error(query.from_user.id, str(e))
        await query.message.reply_text("❌ An error occurred. Please try again.")

async def send_all_files(query, context):
    """Send all files as ZIP with star payment"""
    try:
        await query.message.edit_text("⏳ *Creating ZIP file...*", parse_mode="Markdown")
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for lang, file_info in FILES.items():
                zip_file.writestr(file_info['name'], file_info['content'])
        
        zip_buffer.seek(0)
        
        # Send invoice for payment
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="📦 All Programming Files (ZIP)",
            description="Get all 10 programming template files in one ZIP package!",
            payload=f"zip_all_{query.from_user.id}",
            currency="XTR",  # Telegram Stars currency
            prices=[{"label": "All Files Package", "amount": STAR_PRICE * 10}]
        )
        
        await query.message.edit_text("💳 *Payment invoice sent!*\n\nComplete the payment to receive your files.", parse_mode="Markdown")
        logger.info(f"Payment invoice sent to user {query.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        log_error(query.from_user.id, str(e))
        await query.message.edit_text("❌ Error creating payment. Please try again.")

async def show_file_list(query, context):
    """Show list of individual files"""
    try:
        keyboard = []
        
        for lang, file_info in FILES.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{file_info['emoji']} {file_info['name']} - ⭐{STAR_PRICE}", 
                    callback_data=f"file_{lang}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("« Back", callback_data="back")])
        
        await query.message.edit_text(
            f"📂 *Choose a file to download:*\n\n"
            f"💰 Each file costs ⭐{STAR_PRICE} stars\n\n"
            "Select any programming language file below:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error showing file list: {e}")

async def send_single_file(query, context, lang):
    """Send a single file with star payment"""
    try:
        if lang not in FILES:
            await query.answer("❌ File not found!", show_alert=True)
            return
        
        file_info = FILES[lang]
        await query.answer(f"Preparing invoice for {file_info['name']}...")
        
        # Send invoice for payment
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=f"{file_info['emoji']} {file_info['name']}",
            description=f"{file_info['desc']} - Empty template file ready to use",
            payload=f"file_{lang}_{query.from_user.id}",
            currency="XTR",  # Telegram Stars
            prices=[{"label": file_info['name'], "amount": STAR_PRICE}]
        )
        
        logger.info(f"Payment invoice sent to user {query.from_user.id} for {file_info['name']}")
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        log_error(query.from_user.id, str(e))
        await query.message.reply_text("❌ Error creating payment. Please try again.")

async def show_user_stats(query, context):
    """Show user statistics"""
    try:
        with get_db() as db:
            if db is None:
                await query.answer("Database unavailable", show_alert=True)
                return
            
            user = db.query(User).filter_by(user_id=query.from_user.id).first()
            purchases = get_user_purchases(query.from_user.id)
            
            if user:
                stats_text = (
                    f"📊 *Your Statistics*\n\n"
                    f"👤 User: {user.first_name}\n"
                    f"📅 Joined: {user.join_date.strftime('%Y-%m-%d')}\n"
                    f"🛒 Total Purchases: {user.total_purchases}\n"
                    f"⭐ Total Spent: {user.total_spent} stars\n"
                    f"📆 Last Activity: {user.last_activity.strftime('%Y-%m-%d %H:%M')}\n\n"
                )
                
                if purchases:
                    stats_text += "📜 *Recent Purchases:*\n"
                    for p in purchases[-5:]:
                        stats_text += f"• {p.file_name} - ⭐{p.stars_paid} ({p.purchase_date.strftime('%Y-%m-%d')})\n"
            else:
                stats_text = "No statistics available yet."
        
        keyboard = [[InlineKeyboardButton("« Back", callback_data="back")]]
        await query.message.edit_text(stats_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Error showing user stats: {e}")

async def show_admin_panel(query, context):
    """Show admin panel (admin only)"""
    try:
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("❌ Access denied!", show_alert=True)
            return
        
        stats = get_bot_stats()
        if stats:
            admin_text = (
                f"👑 *Admin Panel*\n\n"
                f"👥 Total Users: {stats['total_users']}\n"
                f"🛒 Total Purchases: {stats['total_purchases']}\n"
                f"💰 Total Revenue: ⭐{stats['total_revenue']} stars\n"
            )
        else:
            admin_text = "Statistics unavailable"
        
        keyboard = [[InlineKeyboardButton("« Back", callback_data="back")]]
        await query.message.edit_text(admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Error showing admin panel: {e}")

async def show_about(query, context):
    """Show about information"""
    try:
        keyboard = [[InlineKeyboardButton("« Back", callback_data="back")]]
        
        await query.message.edit_text(
            "ℹ️ *About This Bot*\n\n"
            "Professional bot for programming templates!\n\n"
            "🐍 Python • 💛 JavaScript • ☕ Java\n"
            "⚡ C++ • 🔷 C# • 🐘 PHP\n"
            "🌐 HTML • 🎨 CSS • 🔵 Go • 🦀 Rust\n\n"
            f"💰 Price: ⭐{STAR_PRICE} stars per file\n"
            f"📦 All files: ⭐{STAR_PRICE*10} stars\n\n"
            "Developer: @YourUsername",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error showing about: {e}")

async def back_to_menu(query, context):
    """Go back to main menu"""
    try:
        user = query.from_user
        keyboard = [
            [InlineKeyboardButton(f"📦 Get All Files (ZIP) - ⭐{STAR_PRICE*10}", callback_data="get_all")],
            [InlineKeyboardButton("📂 Choose Language", callback_data="show_files")],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about")]
        ]
        
        if user.id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])
        
        file_list = "\n".join([f"• {f['emoji']} {f['name']}" for f in FILES.values()])
        
        await query.message.edit_text(
            f"👋 *Welcome {user.first_name}!*\n\n"
            "I can send you empty template files in different languages.\n\n"
            f"📁 *Available Files:*\n{file_list}\n\n"
            f"💰 *Price:* ⭐{STAR_PRICE} stars per file\n\n"
            "Choose an option below:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error going back to menu: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    try:
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
        
        if update and update.effective_user:
            log_error(update.effective_user.id, str(context.error), str(context.error.__traceback__))
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Our team has been notified."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

# ============================================================================
# PAYMENT HANDLERS
# ============================================================================

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pre-checkout queries"""
    query = update.pre_checkout_query
    try:
        # Always approve the checkout
        await query.answer(ok=True)
        logger.info(f"Pre-checkout approved for user {query.from_user.id}")
    except Exception as e:
        logger.error(f"Pre-checkout error: {e}")
        await query.answer(ok=False, error_message="Payment processing error. Please try again.")

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payments"""
    try:
        payment = update.message.successful_payment
        user_id = update.effective_user.id
        payload = payment.invoice_payload
        
        logger.info(f"Payment successful from user {user_id}: {payload}")
        
        # Parse payload to determine what to send
        if payload.startswith("zip_all_"):
            # Send ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for lang, file_info in FILES.items():
                    zip_file.writestr(file_info['name'], file_info['content'])
            
            zip_buffer.seek(0)
            
            await context.bot.send_document(
                chat_id=user_id,
                document=zip_buffer,
                filename="programming_templates.zip",
                caption="✅ *Payment Successful!*\n\n📦 Here are all your programming files!\n\nThank you for your purchase! 🎉",
                parse_mode="Markdown"
            )
            
            add_purchase(user_id, "programming_templates.zip", "zip", STAR_PRICE * 10, payment.telegram_payment_charge_id)
            
        elif payload.startswith("file_"):
            # Send single file
            parts = payload.split("_")
            lang = parts[1]
            
            if lang in FILES:
                file_info = FILES[lang]
                file_buffer = io.BytesIO(file_info['content'].encode('utf-8'))
                file_buffer.name = file_info['name']
                
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file_buffer,
                    filename=file_info['name'],
                    caption=f"✅ *Payment Successful!*\n\n{file_info['emoji']} Here's your {file_info['name']}!\n\nThank you for your purchase! 🎉",
                    parse_mode="Markdown"
                )
                
                add_purchase(user_id, file_info['name'], lang, STAR_PRICE, payment.telegram_payment_charge_id)
        
        await update.message.reply_text(
            "🎉 *Thank you for your purchase!*\n\nYour file has been delivered successfully.\n\nType /start to get more files!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error handling successful payment: {e}")
        log_error(user_id, str(e))
        await update.message.reply_text("❌ Error processing your purchase. Please contact support.")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Start the bot"""
    try:
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Command handlers
        bot_app.add_handler(CommandHandler("start", start))
        
        # Callback handlers
        bot_app.add_handler(CallbackQueryHandler(button_handler))
        
        # Payment handlers
        bot_app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        bot_app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
        
        # Error handler
        bot_app.add_error_handler(error_handler)
        
        logger.info("🚀 Bot started successfully!")
        logger.info("💳 Payment system enabled with Telegram Stars")
        bot_app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
