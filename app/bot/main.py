import logging
import sys
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from app.config.settings import settings
from app.database.connection import init_db
from app.services.sheet_sync import sync_sheet_cache
from app.bot.handlers import (
    start_command, help_command, status_command, sync_command, rekap_command,
    saldo_command, top_command, undo_command, report_command, chart_command, pdf_command,
    handle_text_message, handle_callback_query
)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.log_level.upper(), logging.INFO)
)
logger = logging.getLogger("asisten_bot")


def build_application():
    """Build and configure telegram Application."""
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is missing from .env!")
        sys.exit(1)

    # 1. Initialize SQLite Database
    init_db()

    # 2. Sync Google Sheets cache on startup
    logger.info("Initializing Google Sheets cache sync...")
    sync_sheet_cache()

    # 3. Create Telegram App
    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    # 4. Register Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("sync", sync_command))
    app.add_handler(CommandHandler("rekap", rekap_command))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("chart", chart_command))
    app.add_handler(CommandHandler("pdf", pdf_command))
    app.add_handler(CommandHandler("saldo", saldo_command))
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("undo", undo_command))

    # 5. Register Text & Callback Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    return app


def main():
    """Main execution entrypoint."""
    logger.info("Starting Asisten Keuangan Telegram Bot...")
    app = build_application()
    logger.info("Bot is running & polling for updates...")
    app.run_polling()


if __name__ == "__main__":
    main()
