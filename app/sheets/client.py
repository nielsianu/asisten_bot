import os
from typing import List, Optional
import gspread
from google.oauth2.service_account import Credentials
from app.config.settings import settings
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction


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
                # Handle numeric conversion safely
                def parse_float(val, default=0.0):
                    if isinstance(val, (int, float)):
                        return float(val)
                    try:
                        val_str = str(val).strip()
                        if val_str.startswith("="):
                            return default
                        return float(val_str)
                    except (ValueError, TypeError):
                        return default

                init_bal = parse_float(r.get("Initial Balance"), 0.0)
                curr_bal = parse_float(r.get("Current Balance"), init_bal)
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
        """Fetch all active categories from Categories worksheet."""
        ws = self.spreadsheet.worksheet("Categories")
        records = ws.get_all_records()
        categories = []
        for r in records:
            if str(r.get("Active", "TRUE")).upper() == "TRUE":
                categories.append(Category.from_raw_keywords(
                    id=str(r.get("ID", "")),
                    business=str(r.get("Business", "Household")),
                    type=str(r.get("Type", "Expense")),
                    category_name=str(r.get("Category Name", "")),
                    keywords_str=str(r.get("Keywords", "")),
                    active=True
                ))
        return categories

    def append_transaction(self, tx: Transaction):
        """Append a transaction row to Transactions worksheet."""
        ws = self.spreadsheet.worksheet("Transactions")
        row = tx.to_sheet_row()
        ws.append_row(row, value_input_option="USER_ENTERED")

    def fetch_recent_transactions(self, limit: int = 10) -> List[Transaction]:
        """Fetch recent transactions from Transactions worksheet."""
        ws = self.spreadsheet.worksheet("Transactions")
        records = ws.get_all_records()
        txs = []
        for r in records[-limit:]:
            if r.get("ID"):
                txs.append(Transaction(
                    id=str(r.get("ID")),
                    date=str(r.get("Date")),
                    time=str(r.get("Time")),
                    type=str(r.get("Type")),
                    business=str(r.get("Business")),
                    category=str(r.get("Category")),
                    account=str(r.get("Account")),
                    amount=float(r.get("Amount", 0)),
                    description=str(r.get("Description", "")),
                    source=str(r.get("Source", "Telegram")),
                    ai_confidence=int(r.get("AI Confidence", 100))
                ))
        return txs

    def overwrite_transactions(self, txs: List[Transaction]):
        """Overwrite the entire Transactions worksheet with local SQLite transactions."""
        ws = self.spreadsheet.worksheet("Transactions")
        headers = ["ID", "Date", "Time", "Type", "Business", "Category", "Account", "Amount", "Description", "Source", "AI Confidence"]
        rows = [headers] + [tx.to_sheet_row() for tx in txs]
        ws.clear()
        ws.update(range_name="A1", values=rows)
