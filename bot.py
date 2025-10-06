"""
Telegram Stars Shop Bot
A production-ready bot for selling products using Telegram Stars payment system.

Author: Your Name
Version: 2.0.0
License: MIT
"""

import asyncio
import json
import logging
import os
import signal
import sys
import threading
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Dict, Optional, Callable

from flask import Flask, render_template_string, jsonify
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.error import (
    NetworkError,
    BadRequest,
    TimedOut,
    TelegramError,
    Conflict,
    RetryAfter,
    InvalidToken
)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration from environment variables."""
    BOT_TOKEN: str = "8050433715:AAEtNaKR1cuGfWecar6FR8FSIG2QZqmfkDU"
    PORT: int = int(os.getenv("PORT", 8080))
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://winterlandbot-production.up.railway.app")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_RESTARTS: int = 3
    RETRY_DELAY: int = 2
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging() -> logging.Logger:
    """Configure application logging."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, Config.LOG_LEVEL),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ============================================================================
# DATA MODELS
# ============================================================================

class ProductType(str, Enum):
    """Product type enumeration."""
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"


@dataclass(frozen=True)
class Product:
    """Immutable product data model."""
    id: ProductType
    title: str
    price: int
    description: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id.value,
            "title": self.title,
            "price": self.price,
            "description": self.description
        }


# Product catalog
PRODUCTS: Dict[ProductType, Product] = {
    ProductType.BASIC: Product(
        id=ProductType.BASIC,
        title="📦 الباقة الأساسية",
        price=50,
        description="مثالية للمبتدئين"
    ),
    ProductType.PREMIUM: Product(
        id=ProductType.PREMIUM,
        title="💎 الباقة المميزة",
        price=150,
        description="للمستخدمين المتقدمين"
    ),
    ProductType.VIP: Product(
        id=ProductType.VIP,
        title="👑 الباقة الذهبية",
        price=300,
        description="التجربة الكاملة"
    )
}


# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__)

# HTML template moved to separate constant for better maintainability
WEBAPP_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجر النجوم</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }
        .container { max-width: 500px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; animation: fadeInDown 0.6s ease; }
        .header h1 { font-size: 32px; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .products { display: flex; flex-direction: column; gap: 20px; }
        .product-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            animation: fadeInUp 0.6s ease;
        }
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .product-emoji { font-size: 48px; margin-bottom: 15px; display: block; }
        .product-title { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
        .price-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
        }
        .price { font-size: 28px; font-weight: bold; }
        .buy-btn {
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            color: #000;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .buy-btn:hover { transform: scale(1.05); }
        @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⭐ متجر النجوم ⭐</h1>
        </div>
        <div class="products">
            <div class="product-card">
                <span class="product-emoji">📦</span>
                <div class="product-title">الباقة الأساسية</div>
                <div class="price-section">
                    <div class="price">50 ⭐</div>
                    <button class="buy-btn" onclick="buyProduct('basic', 50)">شراء</button>
                </div>
            </div>
            <div class="product-card">
                <span class="product-emoji">💎</span>
                <div class="product-title">الباقة المميزة</div>
                <div class="price-section">
                    <div class="price">150 ⭐</div>
                    <button class="buy-btn" onclick="buyProduct('premium', 150)">شراء</button>
                </div>
            </div>
            <div class="product-card">
                <span class="product-emoji">👑</span>
                <div class="product-title">الباقة الذهبية</div>
                <div class="price-section">
                    <div class="price">300 ⭐</div>
                    <button class="buy-btn" onclick="buyProduct('vip', 300)">شراء</button>
                </div>
            </div>
        </div>
    </div>
    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();
        
        function buyProduct(productId, price) {
            try {
                tg.sendData(JSON.stringify({ product: productId, price: price }));
            } catch (error) {
                console.error('Error:', error);
                tg.showAlert('حدث خطأ. يرجى المحاولة مرة أخرى.');
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def webapp():
    """Serve the web application."""
    return render_template_string(WEBAPP_HTML)


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'telegram_bot',
        'version': '2.0.0'
    }), 200


@app.route('/favicon.ico')
def favicon():
    """Return empty favicon to prevent 404 errors."""
    return '', 204


# ============================================================================
# ERROR HANDLING
# ============================================================================

def retry_on_error(max_retries: int = 3, delay: int = 2) -> Callable:
    """Decorator for automatic retry on transient errors."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return await func(update, context)
                
                except RetryAfter as e:
                    wait_time = e.retry_after + 1
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                except (NetworkError, TimedOut) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Transient error (attempt {attempt + 1}/{max_retries}): {e}")
                        await asyncio.sleep(delay * (attempt + 1))
                        continue
                    break
                
                except (BadRequest, Conflict, InvalidToken) as e:
                    logger.error(f"Non-retryable error: {e}")
                    raise
                
                except TelegramError as e:
                    last_error = e
                    logger.error(f"Telegram error: {e}")
                    break
                
                except Exception as e:
                    logger.exception(f"Unexpected error: {e}")
                    break
            
            # Send error message to user if possible
            if update and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        "⚠️ حدث خطأ مؤقت. يرجى المحاولة لاحقاً."
                    )
                except:
                    pass
            
            return None
        
        return wrapper
    return decorator


# ============================================================================
# TELEGRAM HANDLERS
# ============================================================================

@retry_on_error(max_retries=3)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update or not update.effective_user:
        return
    
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🛍️ فتح المتجر", web_app=WebAppInfo(url=Config.WEBAPP_URL))],
        [
            InlineKeyboardButton("ℹ️ معلومات", callback_data="info"),
            InlineKeyboardButton("📞 الدعم", callback_data="support")
        ]
    ]
    
    welcome_text = (
        f"🌟 <b>مرحباً {user.first_name}!</b>\n\n"
        f"أهلاً بك في متجر النجوم ⭐\n"
        f"اختر باقتك المفضلة وادفع بنجوم تيليجرام\n\n"
        f"💫 <i>اضغط على 'فتح المتجر' لاستعراض الباقات</i>"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    logger.info(f"User {user.id} started conversation")


@retry_on_error(max_retries=2)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks."""
    query = update.callback_query
    
    try:
        await query.answer()
    except:
        pass
    
    responses = {
        "info": (
            "ℹ️ <b>معلومات المتجر</b>\n\n"
            "🌟 نقبل الدفع بنجوم تيليجرام\n"
            "⚡ معالجة فورية للطلبات\n"
            "🔒 آمن ومضمون 100%"
        ),
        "support": (
            "📞 <b>الدعم الفني</b>\n\n"
            "تواصل معنا:\n"
            "📧 Email: support@example.com\n"
            "💬 Telegram: @support"
        )
    }
    
    text = responses.get(query.data)
    if text:
        await query.edit_message_text(text, parse_mode='HTML')


@retry_on_error(max_retries=3)
async def webapp_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle data received from WebApp."""
    if not update or not update.message or not update.message.web_app_data:
        return
    
    try:
        data = json.loads(update.message.web_app_data.data)
        product_id = data.get('product')
        
        if not product_id:
            await update.message.reply_text("❌ بيانات غير صالحة")
            return
        
        try:
            product_type = ProductType(product_id)
        except ValueError:
            await update.message.reply_text("❌ منتج غير موجود")
            return
        
        product = PRODUCTS[product_type]
        
        # Send processing message
        msg = await update.message.reply_text(
            f"⏳ جاري تجهيز الفاتورة لـ {product.title}..."
        )
        
        # Send invoice
        await context.bot.send_invoice(
            chat_id=update.message.chat_id,
            title=product.title,
            description=product.description,
            payload=f"product_{product.id.value}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(product.title, product.price * 100)]
        )
        
        # Delete processing message
        try:
            await msg.delete()
        except:
            pass
        
        logger.info(f"Invoice sent - User: {update.effective_user.id}, Product: {product_id}")
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON data from WebApp")
        await update.message.reply_text("❌ بيانات غير صالحة")
    except Exception as e:
        logger.exception(f"Error in webapp_data_handler: {e}")
        await update.message.reply_text("❌ حدث خطأ في معالجة طلبك")


@retry_on_error(max_retries=2)
async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pre-checkout query."""
    query = update.pre_checkout_query
    
    if not query or not query.invoice_payload or not query.invoice_payload.startswith("product_"):
        await query.answer(ok=False, error_message="❌ فاتورة غير صالحة")
        return
    
    await query.answer(ok=True)
    logger.info(f"Pre-checkout approved - User: {update.effective_user.id}")


@retry_on_error(max_retries=3)
async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle successful payment."""
    if not update or not update.message or not update.message.successful_payment:
        return
    
    payment = update.message.successful_payment
    
    success_text = (
        "✅ <b>تم الدفع بنجاح!</b>\n\n"
        f"شكراً لشرائك!\n"
        f"المبلغ المدفوع: {payment.total_amount} ⭐\n\n"
        f"تم تفعيل باقتك الآن!"
    )
    
    await update.message.reply_text(success_text, parse_mode='HTML')
    logger.info(f"Payment successful - User: {update.effective_user.id}, Amount: {payment.total_amount}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler."""
    error = context.error
    
    if isinstance(error, (Conflict, InvalidToken)):
        logger.critical(f"Critical error: {error}")
        return
    
    if isinstance(error, RetryAfter):
        logger.warning(f"Rate limited: {error}")
        return
    
    logger.error(f"Unhandled error: {error}", exc_info=error)
    
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ حدث خطأ مؤقت. يرجى المحاولة مرة أخرى."
            )
        except:
            pass


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

class BotApplication:
    """Main bot application manager."""
    
    def __init__(self):
        self.running = True
        self.restart_count = 0
        self.flask_thread: Optional[threading.Thread] = None
        self.application: Optional[Application] = None
    
    def start_flask(self) -> None:
        """Start Flask server in a separate thread."""
        try:
            from waitress import serve
            logger.info(f"Starting Flask with Waitress on port {Config.PORT}")
            serve(app, host='0.0.0.0', port=Config.PORT, threads=4)
        except ImportError:
            logger.warning("Waitress not available, using Flask dev server")
            app.run(host='0.0.0.0', port=Config.PORT, threaded=True, debug=False)
        except Exception as e:
            logger.exception(f"Flask error: {e}")
    
    def setup_signal_handlers(self) -> None:
        """Setup graceful shutdown signal handlers."""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize_bot(self) -> Application:
        """Initialize and configure bot application."""
        application = (
            Application.builder()
            .token(Config.BOT_TOKEN)
            .concurrent_updates(True)
            .connect_timeout(Config.TIMEOUT)
            .read_timeout(Config.TIMEOUT)
            .write_timeout(Config.TIMEOUT)
            .pool_timeout(Config.TIMEOUT)
            .build()
        )
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data_handler))
        application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
        application.add_error_handler(error_handler)
        
        return application
    
    async def run(self) -> None:
        """Main application loop."""
        # Start Flask
        self.flask_thread = threading.Thread(target=self.start_flask, daemon=True)
        self.flask_thread.start()
        logger.info("Flask server started")
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        while self.running and self.restart_count < Config.MAX_RESTARTS:
            try:
                self.application = await self.initialize_bot()
                
                logger.info("Starting bot...")
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                
                # Keep running
                while self.running:
                    await asyncio.sleep(1)
            
            except (Conflict, InvalidToken) as e:
                logger.critical(f"Critical error: {e}")
                self.running = False
                break
            
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                self.running = False
                break
            
            except Exception as e:
                self.restart_count += 1
                logger.exception(
                    f"Error (attempt {self.restart_count}/{Config.MAX_RESTARTS}): {e}"
                )
                
                if self.restart_count < Config.MAX_RESTARTS:
                    logger.info("Restarting in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    logger.critical("Max restarts reached. Stopping.")
                    self.running = False
            
            finally:
                if self.application:
                    try:
                        logger.info("Shutting down bot...")
                        await self.application.stop()
                        await self.application.shutdown()
                    except Exception as e:
                        logger.error(f"Shutdown error: {e}")
        
        logger.info("Bot stopped")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    """Application entry point."""
    try:
        Config.validate()
        bot_app = BotApplication()
        asyncio.run(bot_app.run())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        sys.exit(0)


if __name__ == '__main__':
    main()
