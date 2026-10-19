"""
حلالية - أوامر الإدارة المحمية (نسخة مبسطة بدون decorator)
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.config import ADMIN_IDS
from backend.rate_limiter import rate_limiter
from backend.db import db
from datetime import datetime

logger = logging.getLogger(__name__)


def check_admin(update: Update) -> bool:
    """التحقق من أن المستخدم أدمن"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        logger.warning(f"محاولة وصول غير مصرح بها: {user_id}")
        return False
    return True


async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات النظام للأدمن"""
    if not check_admin(update):
        await update.message.reply_text("🚫 هذا الأمر متاح للمديرين فقط.")
        return

    try:
        products = db.execute_query("SELECT COUNT(*) as count FROM products", fetch=True)
        product_count = products[0]['count'] if products else 0

        halal = db.execute_query("SELECT COUNT(*) as count FROM products WHERE halal_status = 'halal'", fetch=True)
        halal_count = halal[0]['count'] if halal else 0

        message = (
            f"📊 <b>إحصائيات النظام:</b>\n\n"
            f"📦 المنتجات المحللة: {product_count}\n"
            f"✅ المنتجات الحلال: {halal_count}\n"
            f"🔒 Rate Limiting: مفعّل\n\n"
            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"خطأ في admin_stats: {e}", exc_info=True)
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")


async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حظر مستخدم"""
    if not check_admin(update):
        await update.message.reply_text("🚫 هذا الأمر متاح للمديرين فقط.")
        return

    try:
        if not context.args:
            await update.message.reply_text("⚠️ الاستخدام: /ban_user <user_id>")
            return

        user_id = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "بدون سبب"

        rate_limiter.ban_user(user_id, reason)

        await update.message.reply_text(f"✅ تم حظر المستخدم: {user_id}\nالسبب: {reason}")
        logger.info(f"Admin {update.effective_user.id} banned user {user_id}")

    except Exception as e:
        logger.error(f"خطأ في ban_user: {e}", exc_info=True)
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")


async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء حظر مستخدم"""
    if not check_admin(update):
        await update.message.reply_text("🚫 هذا الأمر متاح للمديرين فقط.")
        return

    try:
        if not context.args:
            await update.message.reply_text("⚠️ الاستخدام: /unban_user <user_id>")
            return

        user_id = context.args[0]
        rate_limiter.unban_user(user_id)

        await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم: {user_id}")

    except Exception as e:
        logger.error(f"خطأ في unban_user: {e}", exc_info=True)
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")


async def ban_ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حظر IP"""
    if not check_admin(update):
        await update.message.reply_text("🚫 هذا الأمر متاح للمديرين فقط.")
        return

    try:
        if not context.args:
            await update.message.reply_text("⚠️ الاستخدام: /ban_ip <ip_address>")
            return

        ip = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "بدون سبب"

        rate_limiter.ban_ip(ip, reason)

        await update.message.reply_text(f"✅ تم حظر IP: {ip}\nالسبب: {reason}")

    except Exception as e:
        logger.error(f"خطأ في ban_ip: {e}", exc_info=True)
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")


async def add_trusted_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة مستخدم موثوق"""
    if not check_admin(update):
        await update.message.reply_text("🚫 هذا الأمر متاح للمديرين فقط.")
        return

    try:
        if not context.args:
            await update.message.reply_text("⚠️ الاستخدام: /add_trusted <user_id>")
            return

        user_id = context.args[0]
        rate_limiter.add_trusted_user(user_id)

        await update.message.reply_text(f"✅ تم إضافة المستخدم {user_id} كموثوق")

    except Exception as e:
        logger.error(f"خطأ في add_trusted: {e}", exc_info=True)
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")


async def system_health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص صحة النظام"""
    if not check_admin(update):
        await update.message.reply_text(" هذا الأمر متاح للمديرين فقط.")
        return

    try:
        db_test = db.execute_query("SELECT 1", fetch=True)
        db_status = "✅ تعمل" if db_test else "❌ معطلة"

        stats = rate_limiter.get_usage_stats("system_check", "default")

        message = (
            f"🏥 <b>فحص صحة النظام:</b>\n\n"
            f"🗄️ قاعدة البيانات: {db_status}\n"
            f"🔒 Rate Limiter: ✅ يعمل\n"
            f"📊 الطلبات النشطة: {stats['used']}\n\n"
            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"خطأ في system_health: {e}", exc_info=True)
        await update.message.reply_text(f"❌ فشل فحص النظام: {str(e)}")