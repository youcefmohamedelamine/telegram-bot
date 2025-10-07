"""
Telegram Bot - Send Empty Programming Files in Different Languages
Sends 10 different empty programming files in various languages
Each file costs 999 Telegram Stars
"""

import logging
import io
import zipfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ============================================================================
# CONFIG
# ============================================================================

BOT_TOKEN = "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg"
STAR_PRICE = 999  # سعر كل ملف بالنجوم

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# EMPTY FILES IN DIFFERENT LANGUAGES
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
    keyboard = [
        [InlineKeyboardButton(f"📦 Get All Files (ZIP) - ⭐{STAR_PRICE*10}", callback_data="get_all")],
        [InlineKeyboardButton("📂 Choose Language", callback_data="show_files")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ]
    
    file_list = "\n".join([f"• {f['emoji']} {f['name']}" for f in FILES.values()])
    
    await update.message.reply_text(
        "👋 *Welcome to Programming Files Bot!*\n\n"
        "I can send you empty template files in different languages.\n\n"
        f"📁 *Available Files:*\n{file_list}\n\n"
        f"💰 *Price:* ⭐{STAR_PRICE} stars per file\n\n"
        "Choose an option below:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"User {update.effective_user.id} started bot")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_all":
        await send_all_files(query, context)
    elif query.data == "show_files":
        await show_file_list(query, context)
    elif query.data == "about":
        await show_about(query, context)
    elif query.data == "back":
        await back_to_menu(query, context)
    elif query.data.startswith("file_"):
        lang = query.data.replace("file_", "")
        await send_single_file(query, context, lang)

async def send_all_files(query, context):
    """Send all files as ZIP with star payment"""
    await query.message.edit_text("⏳ *Creating ZIP file...*", parse_mode="Markdown")
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for lang, file_info in FILES.items():
            zip_file.writestr(file_info['name'], file_info['content'])
    
    zip_buffer.seek(0)
    
    # إرسال الملف بسعر النجوم
    await context.bot.send_document(
        chat_id=query.message.chat_id,
        document=zip_buffer,
        filename="programming_templates.zip",
        caption=f"📦 *All Programming Files*\n\nContains 10 files in different languages!\n💰 Price: ⭐{STAR_PRICE*10} stars",
        parse_mode="Markdown",
        star_count=STAR_PRICE * 10  # سعر جميع الملفات
    )
    
    await query.message.edit_text(
        "✅ *ZIP file sent!*\n\nType /start to get more files.",
        parse_mode="Markdown"
    )
    logger.info(f"Sent all files to user {query.from_user.id}")

async def show_file_list(query, context):
    """Show list of individual files"""
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

async def send_single_file(query, context, lang):
    """Send a single file with star payment"""
    if lang not in FILES:
        await query.answer("❌ File not found!", show_alert=True)
        return
    
    file_info = FILES[lang]
    
    await query.answer(f"Sending {file_info['name']}...")
    
    # Create file in memory
    file_buffer = io.BytesIO(file_info['content'].encode('utf-8'))
    file_buffer.name = file_info['name']
    
    # إرسال الملف بسعر النجوم
    await context.bot.send_document(
        chat_id=query.message.chat_id,
        document=file_buffer,
        filename=file_info['name'],
        caption=f"{file_info['emoji']} *{file_info['name']}*\n\n{file_info['desc']}\n💰 Price: ⭐{STAR_PRICE} stars",
        parse_mode="Markdown",
        star_count=STAR_PRICE  # سعر الملف الواحد
    )
    
    logger.info(f"Sent {file_info['name']} to user {query.from_user.id}")

async def show_about(query, context):
    """Show about information"""
    keyboard = [[InlineKeyboardButton("« Back", callback_data="back")]]
    
    await query.message.edit_text(
        "ℹ️ *About This Bot*\n\n"
        "This bot sends empty programming template files in 10 different languages:\n\n"
        "🐍 Python\n"
        "💛 JavaScript\n"
        "☕ Java\n"
        "⚡ C++\n"
        "🔷 C#\n"
        "🐘 PHP\n"
        "🌐 HTML\n"
        "🎨 CSS\n"
        "🔵 Go\n"
        "🦀 Rust\n\n"
        f"💰 *Price:* ⭐{STAR_PRICE} stars per file\n"
        f"📦 All files (ZIP): ⭐{STAR_PRICE*10} stars\n\n"
        "Perfect for starting new projects quickly!\n\n"
        "Developer: @YourUsername",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_to_menu(query, context):
    """Go back to main menu"""
    keyboard = [
        [InlineKeyboardButton(f"📦 Get All Files (ZIP) - ⭐{STAR_PRICE*10}", callback_data="get_all")],
        [InlineKeyboardButton("📂 Choose Language", callback_data="show_files")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ]
    
    file_list = "\n".join([f"• {f['emoji']} {f['name']}" for f in FILES.values()])
    
    await query.message.edit_text(
        "👋 *Welcome to Programming Files Bot!*\n\n"
        "I can send you empty template files in different languages.\n\n"
        f"📁 *Available Files:*\n{file_list}\n\n"
        f"💰 *Price:* ⭐{STAR_PRICE} stars per file\n\n"
        "Choose an option below:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Start the bot"""
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(button_handler))
    bot_app.add_error_handler(error_handler)
    
    logger.info("🚀 Bot started!")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
