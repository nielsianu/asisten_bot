import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.database.repository import CacheRepository, TransactionRepository

logger = logging.getLogger(__name__)

MONTH_NAMES_ID = {
    "01": "Januari", "02": "Februari", "03": "Maret", "04": "April",
    "05": "Mei", "06": "Juni", "07": "Juli", "08": "Agustus",
    "09": "September", "10": "Oktober", "11": "November", "12": "Desember"
}

MONTH_MAP = {
    "januari": "01", "january": "01", "jan": "01", "01": "01", "1": "01",
    "februari": "02", "february": "02", "feb": "02", "02": "02", "2": "02",
    "maret": "03", "march": "03", "mar": "03", "03": "03", "3": "03",
    "april": "04", "apr": "04", "04": "04", "4": "04",
    "mei": "05", "may": "05", "05": "05", "5": "05",
    "juni": "06", "june": "06", "jun": "06", "06": "06", "6": "06",
    "juli": "07", "july": "07", "jul": "07", "07": "07", "7": "07",
    "agustus": "08", "august": "08", "aug": "08", "08": "08", "8": "08",
    "september": "09", "sep": "09", "sept": "09", "09": "09", "9": "09",
    "oktober": "10", "october": "10", "okt": "10", "oct": "10", "10": "10",
    "november": "11", "nov": "11", "11": "11",
    "desember": "12", "december": "12", "des": "12", "dec": "12", "12": "12"
}


def parse_target_month(args: List[str]) -> str:
    """Parse month and year from command args (e.g. ['juni', '2026'] or ['2026-06'])."""
    now = datetime.now()
    default_year = str(now.year)
    default_month = now.strftime("%m")

    if not args:
        return f"{default_year}-{default_month}"

    joined = " ".join(args).lower().strip()

    # Case YYYY-MM
    if len(joined) == 7 and joined[4] == "-":
        return joined

    month_code = None
    year_code = default_year

    for token in args:
        t_clean = token.lower().strip()
        if t_clean in MONTH_MAP:
            month_code = MONTH_MAP[t_clean]
        elif t_clean.isdigit() and len(t_clean) == 4:
            year_code = t_clean

    if not month_code:
        month_code = default_month

    return f"{year_code}-{month_code}"


class DashboardService:
    """Service to compute financial summaries for Household and Catering."""

    @staticmethod
    def get_summary(target_month: Optional[str] = None) -> Dict[str, Any]:
        """Compute financial balances and metrics for a specific month (YYYY-MM).
        Uses Google Sheets as primary live database, falling back to local SQLite cache if offline.
        """
        is_live = False
        accounts = []
        recent_txs = []

        # 1. Primary: Try fetching live data from Google Sheets
        try:
            from app.sheets.client import SheetsClient
            sheets_client = SheetsClient()
            sheet_accounts = sheets_client.fetch_accounts()
            sheet_txs = sheets_client.fetch_all_transactions()

            if sheet_accounts:
                accounts = sheet_accounts
                CacheRepository.cache_accounts(accounts)

            if sheet_txs:
                recent_txs = sheet_txs
                TransactionRepository.sync_transactions_from_sheet(sheet_txs)

            # Also check if there are any local unsynced offline txs to include
            unsynced = TransactionRepository.get_unsynced_transactions()
            if unsynced:
                existing_ids = {t.id for t in recent_txs}
                for u_tx in unsynced:
                    if u_tx.id not in existing_ids:
                        recent_txs.append(u_tx)

            is_live = True
        except Exception as e:
            logger.warning(f"Google Sheets live fetch failed: {e}. Falling back to SQLite backup cache.")
            accounts = CacheRepository.get_cached_accounts()
            recent_txs = TransactionRepository.get_recent_transactions(limit=1000)

        if not target_month:
            target_month = datetime.now().strftime("%Y-%m")

        year_str, month_num = target_month.split("-")
        month_name = MONTH_NAMES_ID.get(month_num, month_num)
        formatted_month_label = f"{month_name} {year_str}"

        month_txs = [t for t in recent_txs if t.date.startswith(target_month)]

        total_income = sum(t.amount for t in month_txs if t.type == "Income")
        total_expense = sum(t.amount for t in month_txs if t.type == "Expense")
        net_cash_flow = total_income - total_expense

        catering_income = sum(t.amount for t in month_txs if t.business == "Catering" and t.type == "Income")
        catering_expense = sum(t.amount for t in month_txs if t.business == "Catering" and t.type == "Expense")
        catering_profit = catering_income - catering_expense

        # Expenses grouped by category
        expenses_by_cat: Dict[str, float] = {}
        for t in month_txs:
            if t.type == "Expense":
                expenses_by_cat[t.category] = expenses_by_cat.get(t.category, 0.0) + t.amount

        sorted_top_expenses = sorted(expenses_by_cat.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "accounts": accounts,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_cash_flow": net_cash_flow,
            "catering_income": catering_income,
            "catering_expense": catering_expense,
            "catering_profit": catering_profit,
            "top_expenses": sorted_top_expenses,
            "month": target_month,
            "month_label": formatted_month_label,
            "month_transactions": month_txs[:10],  # Top 10 recent transactions for target month
            "is_live": is_live
        }
