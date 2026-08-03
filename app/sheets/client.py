import os
import re
import logging
from typing import List, Optional, Dict
import gspread
from google.oauth2.service_account import Credentials
from app.config.settings import settings
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


def parse_currency_num(val, default: float = 0.0) -> float:
    """Safely parse numbers from Google Sheets cells containing IDR formatting (e.g. 'Rp 2.000.000,00', '2.500.000', etc.)."""
    if isinstance(val, (int, float)):
        return float(val)
    if not val:
        return default
    try:
        val_str = str(val).strip()
        if val_str.startswith("="):
            return default
        # Remove currency symbols (Rp, rp, RP) and non-numeric chars except digits, dots, commas
        clean = re.sub(r"[^\d\.,]", "", val_str)
        if not clean:
            return default

        if "." in clean and "," in clean:
            if clean.find(".") < clean.find(","):  # e.g. 2.000.000,00
                clean = clean.replace(".", "").replace(",", ".")
            else:  # e.g. 2,000,000.00
                clean = clean.replace(",", "")
        elif "." in clean:
            if clean.count(".") > 1:  # e.g. 2.000.000
                clean = clean.replace(".", "")
            else:
                parts = clean.split(".")
                if len(parts[1]) == 3:  # IDR thousand separator e.g. 250.000
                    clean = clean.replace(".", "")
        elif "," in clean:
            if clean.count(",") > 1:  # e.g. 2,000,000
                clean = clean.replace(",", "")
            else:
                parts = clean.split(",")
                if len(parts[1]) == 3:
                    clean = clean.replace(",", "")
                else:
                    clean = clean.replace(",", ".")

        return float(clean)
    except Exception:
        return default


class SheetsClient:
    """Client for Google Sheets API operations."""

    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None

    def connect(self):
        """Establish connection to Google Sheets API."""
        if not os.path.exists(settings.google_credentials_file):
            raise FileNotFoundError(f"Credentials file '{settings.google_credentials_file}' not found.")
        if not settings.google_sheet_id:
            raise ValueError("GOOGLE_SHEET_ID is not configured in .env.")

        credentials = Credentials.from_service_account_file(
            settings.google_credentials_file, scopes=self.scopes
        )
        self._client = gspread.authorize(credentials)
        self._spreadsheet = self._client.open_by_key(settings.google_sheet_id)

    @property
    def spreadsheet(self) -> gspread.Spreadsheet:
        if self._spreadsheet is None:
            self.connect()
        return self._spreadsheet

    def fetch_accounts(self) -> List[Account]:
        """Fetch all active accounts from Accounts worksheet."""
        ws = self.spreadsheet.worksheet("Accounts")
        records = ws.get_all_records()
        accounts = []
        for r in records:
            if str(r.get("Active", "TRUE")).upper() == "TRUE":
                init_bal = parse_currency_num(r.get("Initial Balance"), 0.0)
                curr_bal = parse_currency_num(r.get("Current Balance"), init_bal)
                accounts.append(Account(
                    id=str(r.get("ID", "")),
                    account_name=str(r.get("Account Name", "")),
                    type=str(r.get("Type", "Cash")),
                    initial_balance=init_bal,
                    current_balance=curr_bal,
                    notes=str(r.get("Notes", "")),
                    active=True
                ))
        return accounts

    def fetch_categories(self) -> List[Category]:
        """Fetch all active categories from Categories worksheet (including Column G Budget)."""
        ws = self.spreadsheet.worksheet("Categories")
        records = ws.get_all_records()
        categories = []
        for r in records:
            if str(r.get("Active", "TRUE")).upper() == "TRUE":
                budget_val = str(r.get("Budget", r.get("budget", ""))).strip()
                categories.append(Category.from_raw_keywords(
                    id=str(r.get("ID", "")),
                    business=str(r.get("Business", "Household")),
                    type=str(r.get("Type", "Expense")),
                    category_name=str(r.get("Category Name", "")),
                    keywords_str=str(r.get("Keywords", "")),
                    budget_category=budget_val if budget_val else None,
                    active=True
                ))
        return categories

    def fetch_budgets(self) -> Dict[str, float]:
        """Fetch budget limits directly from Budget worksheet (Category & Monthly Budget columns)."""
        try:
            ws = self.spreadsheet.worksheet("Budget")
            records = ws.get_all_records()
            budgets = {}
            for r in records:
                cat_name = str(r.get("Category", r.get("Kategori", ""))).strip()
                raw_amt = r.get("Monthly Budget", r.get("Amount", r.get("Budget", 0)))
                amt_val = parse_currency_num(raw_amt, 0.0)

                if cat_name and amt_val > 0:
                    budgets[cat_name] = amt_val
            return budgets
        except Exception as e:
            logger.warning(f"Error fetching Budget worksheet: {e}")
            return {}

    def append_transaction(self, tx: Transaction):
        """Append a transaction row to Transactions worksheet."""
        ws = self.spreadsheet.worksheet("Transactions")
        row = tx.to_sheet_row()
        ws.append_row(row, value_input_option="USER_ENTERED")

    def fetch_all_transactions(self) -> List[Transaction]:
        """Fetch all transactions from Transactions worksheet."""
        ws = self.spreadsheet.worksheet("Transactions")
        records = ws.get_all_records()
        txs = []
        for r in records:
            if r.get("ID"):
                def parse_int(val, default=100):
                    if isinstance(val, int):
                        return val
                    try:
                        return int(val)
                    except Exception:
                        return default

                txs.append(Transaction(
                    id=str(r.get("ID")),
                    date=str(r.get("Date", "")),
                    time=str(r.get("Time", "")),
                    type=str(r.get("Type", "Expense")),
                    business=str(r.get("Business", "Household")),
                    category=str(r.get("Category", "Lainnya")),
                    account=str(r.get("Account", "Cash")),
                    amount=parse_currency_num(r.get("Amount", 0)),
                    description=str(r.get("Description", "")),
                    source=str(r.get("Source", "Telegram")),
                    ai_confidence=parse_int(r.get("AI Confidence", 100))
                ))
        return txs

    def fetch_recent_transactions(self, limit: int = 1000) -> List[Transaction]:
        """Fetch recent transactions from Transactions worksheet."""
        all_txs = self.fetch_all_transactions()
        return all_txs[-limit:] if limit > 0 else all_txs

    def overwrite_transactions(self, txs: List[Transaction]):
        """Overwrite the entire Transactions worksheet with local SQLite transactions."""
        ws = self.spreadsheet.worksheet("Transactions")
        headers = ["ID", "Date", "Time", "Type", "Business", "Category", "Account", "Amount", "Description", "Source", "AI Confidence"]
        rows = [headers] + [tx.to_sheet_row() for tx in txs]
        ws.clear()
        ws.update(range_name="A1", values=rows)
