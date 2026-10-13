from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.api_client import analyze_product
from telegram_bot.formatter import (
    format_product,
    format_compare
)


# ==========================================
# HANDLE USER MESSAGE
# ==========================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    if not text:

        await update.message.reply_text(
            "⚠️ اكتب اسم منتج."
        )

        return

    # ======================================
    # PRODUCT COMPARISON
    # ======================================

    if "vs" in text.lower():

        parts = text.split("vs")

        if len(parts) != 2:

            await update.message.reply_text(
                "مثال:\n\n"
                "iphone vs samsung"
            )

            return

        product1 = parts[0].strip()
        product2 = parts[1].strip()

        result1 = analyze_product(product1)
        result2 = analyze_product(product2)

        if "error" in result1:

            await update.message.reply_text(
                f"❌ {result1['error']}"
            )

            return

        if "error" in result2:

            await update.message.reply_text(
                f"❌ {result2['error']}"
            )

            return

        await update.message.reply_text(

            format_compare(
                result1,
                result2
            )

        )

        return

    # ======================================
    # SINGLE PRODUCT
    # ======================================

    data = analyze_product(text)

    if "error" in data:

        errors = {

            "SERVER_OFF": "🔌 السيرفر غير شغال",

            "TIMEOUT": "⏳ انتهت المهلة",

            "INVALID_JSON": "❌ خطأ فى السيرفر"

        }

        await update.message.reply_text(

            errors.get(
                data["error"],
                data["error"]
            )

        )

        return

    await update.message.reply_text(

        format_product(data)

    )