import logging
from app.sheets.client import SheetsClient
from app.database.repository import CacheRepository

logger = logging.getLogger(__name__)


def sync_sheet_cache():
    """Sync Accounts and Categories from Google Sheets into local SQLite cache."""
    try:
        sheets_client = SheetsClient()
        accounts = sheets_client.fetch_accounts()
        categories = sheets_client.fetch_categories()

        CacheRepository.cache_accounts(accounts)
        CacheRepository.cache_categories(categories)

        logger.info(f"Sync completed successfully. Cached {len(accounts)} accounts and {len(categories)} categories.")
        return True, len(accounts), len(categories)
    except Exception as e:
        logger.error(f"Sync sheet cache failed: {e}", exc_info=True)
        return False, 0, 0
