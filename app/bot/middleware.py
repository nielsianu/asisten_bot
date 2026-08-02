import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.config.settings import settings

logger = logging.getLogger(__name__)


def is_user_allowed(user) -> bool:
    """Check if Telegram user is allowed based on user ID or username."""
    if not user:
        return False
    allowed_list = settings.allowed_users
    if not allowed_list:
        return True  # If empty, allow (or warning mode)

    user_id_str = str(user.id).lower()
    username_str = (user.username or "").lstrip("@").lower()

    if user_id_str in allowed_list or username_str in allowed_list:
        return True

    logger.warning(f"Unauthorized access attempt by User ID: {user.id}, Username: @{user.username}")
    return False


async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Middleware handler to verify authorization."""
    user = update.effective_user
    if not is_user_allowed(user):
        if update.message:
            await update.message.reply_text("🚫 Akses ditolak. Anda tidak terdaftar sebagai pengguna resmi bot ini.")
        return False
    return True
