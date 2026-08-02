import os
import pytest
from app.config.settings import settings
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.database.connection import init_db
from app.database.repository import TransactionRepository, CacheRepository
from app.sheets.client import SheetsClient


def test_settings_loading():
    """Verify settings loaded correctly from .env."""
    assert settings.telegram_bot_token != ""
    assert "danil2guna" in settings.allowed_users
    assert settings.google_sheet_id != ""


def test_domain_models():
    """Verify Account, Category, and Transaction model validation."""
    acc = Account(id="ACC-001", account_name="Cash", type="Cash")
    assert acc.id == "ACC-001"
    assert acc.active is True

    cat = Category.from_raw_keywords(
        id="CAT-001", business="Household", type="Expense", category_name="Belanja Dapur", keywords_str="beras, sayur"
    )
    assert "beras" in cat.keywords
    assert "sayur" in cat.keywords

    tx = Transaction(
        type="Expense", business="Household", category="Belanja Dapur",
        account="Cash", amount=150000, description="Beli beras dan minyak"
    )
    assert tx.amount == 150000
    assert len(tx.to_sheet_row()) == 11


def test_database_and_repository(tmp_path):
    """Test SQLite database initialization and repository methods."""
    db_file = tmp_path / "test.db"
    original_db = settings.database_path
    settings.database_path = str(db_file)

    try:
        init_db()

        tx = Transaction(
            type="Expense", business="Household", category="Jajan",
            account="Blu BCA", amount=25000, description="Kopi susu"
        )
        TransactionRepository.save_transaction(tx)

        recent = TransactionRepository.get_recent_transactions(limit=5)
        assert len(recent) == 1
        assert recent[0].description == "Kopi susu"

        accounts = [Account(id="ACC-TEST", account_name="Test Bank", type="Bank")]
        CacheRepository.cache_accounts(accounts)
        cached_accs = CacheRepository.get_cached_accounts()
        assert len(cached_accs) == 1
        assert cached_accs[0].account_name == "Test Bank"
    finally:
        settings.database_path = original_db


def test_google_sheets_connection():
    """Test connection to live Google Sheets API."""
    client = SheetsClient()
    accounts = client.fetch_accounts()
    categories = client.fetch_categories()

    assert len(accounts) > 0
    assert len(categories) > 0
    assert any(a.account_name == "Cash" for a in accounts)
    assert any(c.category_name == "Belanja Dapur" for c in categories)
