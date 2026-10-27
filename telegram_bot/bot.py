"""
HALALIA Telegram Bot - Main Entry Point
المؤسس: جمال الدين زيدان
"""
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from pathlib import Path

# تحميل الإعدادات
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from telegram_bot.config import BOT_TOKEN, ADMIN_ID_LIST, ENVIRONMENT

# استيراد الدوال الموجودة فقط
from telegram_bot.commands import (
    start_command,
    help_command,
    stats_command,
    top_command,
    delete_command,
    compare_command,
    save_command,
    favorites_command,
    unsave_command,
    report_command,
    alternatives_command,
    recommend_command,
)

from telegram_bot.handlers import handle_message

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def rate_limit(key):
    """محدد معدل الطلبات البسيط"""
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            return await func(update, context)
        return wrapper
    return decorator


def main():
    """تشغيل البوت"""
    print("🌸 ...الآن تعمل حلالية")
    print(f"👤 Admin IDs: {ADMIN_ID_LIST}")
    print(f"🌍 Environment: {ENVIRONMENT}")
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # تسجيل الأوامر الموجودة فقط
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(CommandHandler("compare", compare_command))
    application.add_handler(CommandHandler("save", save_command))
    application.add_handler(CommandHandler("favorites", favorites_command))
    application.add_handler(CommandHandler("unsave", unsave_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("alternatives", alternatives_command))
    application.add_handler(CommandHandler("recommend", recommend_command))
    
    # معالج الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالج الأزرار التفاعلية
    # application.add_handler(CallbackQueryHandler(handle_button))
    
    # تشغيل البوت
    print("✅ Bot Token loaded successfully")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()