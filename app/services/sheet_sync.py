import logging
from app.sheets.client import SheetsClient
from app.database.repository import CacheRepository

logger = logging.getLogger(__name__)


def sync_sheet_cache():
    """Sync Accounts, Categories, and Transactions from Google Sheets into local SQLite cache.
    Also pushes any unsynced local offline transactions to Google Sheets.
    """
    try:
        from app.database.repository import TransactionRepository
        sheets_client = SheetsClient()

        # 1. Push any unsynced local offline transactions to Google Sheets
        unsynced_txs = TransactionRepository.get_unsynced_transactions()
        pushed_count = 0
        for tx in unsynced_txs:
            try:
                sheets_client.append_transaction(tx)
                TransactionRepository.mark_as_synced(tx.id)
                pushed_count += 1
            except Exception as e:
                logger.error(f"Failed to push unsynced tx {tx.id} during sync: {e}")

        # 2. Fetch latest data from Google Sheets primary database
        accounts = sheets_client.fetch_accounts()
        categories = sheets_client.fetch_categories()
        transactions = sheets_client.fetch_all_transactions()

        # 3. Update local SQLite backup mirror
        if accounts:
            CacheRepository.cache_accounts(accounts)
        if categories:
            CacheRepository.cache_categories(categories)
        if transactions:
            TransactionRepository.sync_transactions_from_sheet(transactions)

        logger.info(f"Sync completed successfully. Cached {len(accounts)} accounts, {len(categories)} categories, {len(transactions)} transactions. Pushed {pushed_count} offline transactions.")
        return True, len(accounts), len(categories), len(transactions), pushed_count
    except Exception as e:
        logger.error(f"Sync sheet cache failed: {e}", exc_info=True)
        return False, 0, 0, 0, 0
