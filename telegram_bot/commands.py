from telegram import Update
from telegram.ext import ContextTypes

from backend.trending_products import TRENDING_PRODUCTS

from telegram_bot.api_client import (
    get_saved_products,
    get_hunt_products
)

from telegram_bot.formatter import (
    format_saved,
    format_hunt
)


# ==========================================
# START
# ==========================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = (
        "🤖 أهلاً بك في AI Product Hunter\n\n"
        "اكتب اسم أي منتج وسأقوم بتحليله بالكامل.\n\n"
        "الأوامر المتاحة:\n"
        "/top\n"
        "/topsaved\n"
        "/hunt"
    )

    await update.message.reply_text(message)


# ==========================================
# TOP
# ==========================================

async def top_products(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = "🔥 أفضل المنتجات المقترحة حالياً\n\n"

    for index, product in enumerate(
        TRENDING_PRODUCTS,
        start=1
    ):

        message += f"{index}- {product}\n"

    await update.message.reply_text(message)


# ==========================================
# SAVED
# ==========================================

async def top_saved(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    products = get_saved_products()

    message = format_saved(products)

    await update.message.reply_text(message)


# ==========================================
# HUNT
# ==========================================

async def hunt_products(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    products = get_hunt_products()

    message = format_hunt(products)

    await update.message.reply_text(message)