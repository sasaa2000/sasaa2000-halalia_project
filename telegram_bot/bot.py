import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters
)

from config import BOT_TOKEN

from telegram_bot.commands import (
    start,
    top_products,
    top_saved,
    hunt_products
)

from telegram_bot.handlers import (
    handle_message
)


# ==========================================
# MAIN
# ==========================================

def main():

    if not BOT_TOKEN:

        print("❌ BOT TOKEN NOT FOUND")

        return

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    # ======================
    # Commands
    # ======================

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "top",
            top_products
        )
    )

    app.add_handler(
        CommandHandler(
            "topsaved",
            top_saved
        )
    )

    app.add_handler(
        CommandHandler(
            "hunt",
            hunt_products
        )
    )

    # ======================
    # Messages
    # ======================

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("🤖 AI Product Hunter Running...")

    app.run_polling()


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    main()