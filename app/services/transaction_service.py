import logging
from typing import Tuple, Optional
from app.models.transaction import Transaction
from app.database.repository import TransactionRepository
from app.sheets.client import SheetsClient
from app.parser.base import ParsedResult

logger = logging.getLogger(__name__)


class TransactionService:
    """Service to process, save, and undo transactions."""

    @staticmethod
    def create_from_parsed(parsed: ParsedResult) -> Transaction:
        """Construct a Transaction model from a ParsedResult."""
        return Transaction(
            type=parsed.type,
            business=parsed.business,
            category=parsed.category,
            account=parsed.account,
            amount=parsed.amount,
            description=parsed.description,
            source="Telegram",
            ai_confidence=parsed.confidence
        )

    @staticmethod
    def save_transaction(tx: Transaction) -> Tuple[bool, str]:
        """Save transaction directly to primary database (Google Sheets) and update SQLite mirror."""
        try:
            # 1. Append directly to primary database (Google Sheets)
            sheets_client = SheetsClient()
            sheets_client.append_transaction(tx)

            # 2. Update local SQLite mirror cache with synced=True
            TransactionRepository.save_transaction(tx, synced=True)

            logger.info(f"Transaction {tx.id} saved successfully to primary database (Google Sheets).")
            return True, f"Status: Berhasil dicatat ke Google Sheets (ID: {tx.id})"
        except Exception as e:
            logger.error(f"Failed to append transaction {tx.id} to Google Sheets: {e}", exc_info=True)
            # Offline backup: Save locally to SQLite with synced=False
            TransactionRepository.save_transaction(tx, synced=False)
            return False, f"Status: Saved to offline backup cache (Google Sheets connection error: {e})"

    @staticmethod
    def undo_last_transaction() -> Tuple[bool, str]:
        """Delete the most recent transaction from SQLite cache."""
        recent_txs = TransactionRepository.get_recent_transactions(limit=1)
        if not recent_txs:
            return False, "Tidak ada transaksi terbaru untuk dibatalkan."

        last_tx = recent_txs[0]
        deleted = TransactionRepository.delete_transaction(last_tx.id)
        if deleted:
            logger.info(f"Transaction {last_tx.id} undone locally.")
            return True, f"↩️ Transaksi ID `{last_tx.id}` (*Rp {last_tx.amount:,.0f}* - {last_tx.description}) telah dibatalkan."
        return False, "Gagal membatalkan transaksi."
