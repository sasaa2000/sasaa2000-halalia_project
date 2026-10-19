"""
حلالية - Main Entry Point مع حماية أمنية كاملة
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

from telegram_bot.admin_commands import (
    admin_stats_command, ban_user_command, unban_user_command,
    ban_ip_command, add_trusted_command, system_health_command
)
from telegram_bot.config import BOT_TOKEN, ADMIN_IDS, MAX_INPUT_LENGTH
from telegram_bot.commands import (
    start_command, stats_command, top_command, delete_command,
    compare_command, help_command, save_command, favorites_command,
    unsave_command, report_command, alternatives_command,
    process_alert, myalerts_command, cancelalert_command,
    category_command, gifts_command, wishlist_command,
    review_command, profile_command, halal_guide_command,
    daily_pick_command,
)
from telegram_bot.handlers import handle_message, button_callback
from telegram_bot.validators import input_validator
from backend.rate_limiter import rate_limiter

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ==========================================
# Rate Limiting Decorator
# ==========================================

def rate_limit(action='default'):
    """Decorator للحد من الطلبات"""

    def decorator(handler):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = str(update.effective_user.id)
            username = update.effective_user.username or "unknown"

            # الحصول على IP (إن أمكن)
            ip = None
            if update.effective_message and hasattr(update.effective_message, 'connection'):
                ip = update.effective_message.connection

            # التحقق من Rate Limiting
            result = rate_limiter.is_allowed(user_id, action, ip)

            if not result['allowed']:
                logger.warning(f"تجاوز الحد: {user_id} (@{username}) - {action}")
                await update.message.reply_text(result['message'])
                return

            # تنفيذ الـ handler
            await handler(update, context)

        return wrapper

    return decorator


# ==========================================
# Input Validation Middleware
# ==========================================

async def validate_input(update: Update, context: ContextTypes.DEFAULT_TYPE, handler):
    """Middleware للتحقق من المدخلات"""
    if update.message and update.message.text:
        text = update.message.text

        # التحقق من النص
        is_valid, error_msg = input_validator.validate_text(text)

        if not is_valid:
            logger.warning(f"مدخل غير صالح من {update.effective_user.id}: {text[:50]}")
            await update.message.reply_text(error_msg)
            return

        # تنفيذ الـ handler
        await handler(update, context)
    else:
        await handler(update, context)


# ==========================================
# Error Handler
# ==========================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء بشكل آمن"""
    logger.error(f"Exception: {context.error}")

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "عذراً، حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.\n\n"
            "إذا استمرت المشكلة، استخدم /report للإبلاغ."
        )


# ==========================================
# Main Function
# ==========================================

def main():
    if not BOT_TOKEN:
        print("❌ BOT TOKEN NOT FOUND")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # إضافة handlers مع Rate Limiting
    application.add_handler(CommandHandler("start", rate_limit('default')(start_command)))
    application.add_handler(CommandHandler("stats", rate_limit('search')(stats_command)))
    application.add_handler(CommandHandler("top", rate_limit('search')(top_command)))
    application.add_handler(CommandHandler("delete", rate_limit('default')(delete_command)))
    application.add_handler(CommandHandler("compare", rate_limit('analyze')(compare_command)))
    application.add_handler(CommandHandler("help", rate_limit('default')(help_command)))
    application.add_handler(CommandHandler("save", rate_limit('save')(save_command)))
    application.add_handler(CommandHandler("favorites", rate_limit('search')(favorites_command)))
    application.add_handler(CommandHandler("unsave", rate_limit('save')(unsave_command)))
    application.add_handler(CommandHandler("report", rate_limit('default')(report_command)))
    application.add_handler(CommandHandler("alternatives", rate_limit('search')(alternatives_command)))
    application.add_handler(CommandHandler("alert", rate_limit('alert')(process_alert)))
    application.add_handler(CommandHandler("myalerts", rate_limit('search')(myalerts_command)))
    application.add_handler(CommandHandler("cancelalert", rate_limit('alert')(cancelalert_command)))
    application.add_handler(CommandHandler("category", rate_limit('search')(category_command)))
    application.add_handler(CommandHandler("gifts", rate_limit('search')(gifts_command)))
    application.add_handler(CommandHandler("wishlist", rate_limit('wishlist')(wishlist_command)))
    application.add_handler(CommandHandler("review", rate_limit('review')(review_command)))
    application.add_handler(CommandHandler("profile", rate_limit('default')(profile_command)))
    application.add_handler(CommandHandler("halal_guide", rate_limit('default')(halal_guide_command)))
    application.add_handler(CommandHandler("daily", rate_limit('default')(daily_pick_command)))
    # أوامر الإدارة (بدون decorator)
    from telegram_bot.admin_commands import (
        admin_stats_command, ban_user_command, unban_user_command,
        ban_ip_command, add_trusted_command, system_health_command
    )

    application.add_handler(CommandHandler("admin_stats", admin_stats_command))
    application.add_handler(CommandHandler("ban_user", ban_user_command))
    application.add_handler(CommandHandler("unban_user", unban_user_command))
    application.add_handler(CommandHandler("ban_ip", ban_ip_command))
    application.add_handler(CommandHandler("add_trusted", add_trusted_command))
    application.add_handler(CommandHandler("system_health", system_health_command))

    # Message Handler مع Rate Limiting و Input Validation
    async def rate_limited_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)

        # التحقق من Rate Limiting
        result = rate_limiter.is_allowed(user_id, 'analyze')
        if not result['allowed']:
            await update.message.reply_text(result['message'])
            return

        # التحقق من المدخلات
        if update.message.text:
            is_valid, error_msg = input_validator.validate_text(update.message.text)
            if not is_valid:
                await update.message.reply_text(error_msg)
                return

        await handle_message(update, context)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, rate_limited_message_handler))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)

    print("🌸 منصة حلالية للذكاء الاصطناعي الحلال تعمل الآن...")
    print("🔒 نظام الحماية الأمني مفعل بالكامل")
    print(f" Admin IDs: {ADMIN_IDS}")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()