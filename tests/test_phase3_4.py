import pytest
from unittest.mock import MagicMock, patch
from app.services.dashboard_service import DashboardService
from app.ai.client import NineRouterClient
from app.parser.base import ParsedResult
from app.models.account import Account
from app.models.transaction import Transaction
from app.database.repository import TransactionRepository, CacheRepository
from app.database.connection import init_db
from app.config.settings import settings


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_file = tmp_path / "test_phase3_4.db"
    original_db = settings.database_path
    settings.database_path = str(db_file)
    init_db()
    yield
    settings.database_path = original_db


def test_dashboard_service_summary():
    """Test dashboard calculations for income, expense, and catering profit."""
    # Seed mock accounts
    CacheRepository.cache_accounts([
        Account(id="1", account_name="Cash", type="Cash", current_balance=500000),
        Account(id="2", account_name="BCA", type="Bank", current_balance=2000000)
    ])

    # Seed mock transactions
    TransactionRepository.save_transaction(Transaction(
        type="Expense", business="Household", category="Belanja Dapur", account="Cash", amount=150000, description="Sayur"
    ))
    TransactionRepository.save_transaction(Transaction(
        type="Income", business="Catering", category="Penjualan", account="BCA", amount=1000000, description="Pesanan Nasi Box"
    ))
    TransactionRepository.save_transaction(Transaction(
        type="Expense", business="Catering", category="Bahan Baku", account="BCA", amount=400000, description="Daging katering"
    ))

    summary = DashboardService.get_summary()

    assert summary["total_income"] == 1000000.0
    assert summary["total_expense"] == 550000.0
    assert summary["net_cash_flow"] == 450000.0
    assert summary["catering_income"] == 1000000.0
    assert summary["catering_expense"] == 400000.0
    assert summary["catering_profit"] == 600000.0
    assert len(summary["top_expenses"]) >= 1


@patch("requests.post")
def test_ninerouter_ai_client(mock_post):
    """Test 9Router AI response parsing."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"type": "Expense", "business": "Household", "category": "Belanja Dapur", "account": "Blu BCA", "amount": 350000, "description": "Beli sembako komplit"}'
                }
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    client = NineRouterClient()
    res = client.parse_ambiguous_text("kemarin daku beli sembako komplit 350rb pakai blu")

    assert res.success is True
    assert res.amount == 350000.0
    assert res.account == "Blu BCA"
    assert res.category == "Belanja Dapur"
    assert res.confidence == 85


def test_parse_target_month():
    """Test month & year argument parsing."""
    from app.services.dashboard_service import parse_target_month

    assert parse_target_month(["juni", "2026"]) == "2026-06"
    assert parse_target_month(["06", "2026"]) == "2026-06"
    assert parse_target_month(["2026-06"]) == "2026-06"
    assert parse_target_month(["juli"]) == f"{pytest.importorskip('datetime').datetime.now().year}-07"


@patch("requests.post")
def test_ai_financial_qna(mock_post):
    """Test 9Router AI Q&A response for natural language questions."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Total pengeluaran Anda bulan ini adalah Rp 550.000."
                }
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    summary_data = {
        "month_label": "Agustus 2026",
        "total_income": 1000000.0,
        "total_expense": 550000.0,
        "net_cash_flow": 450000.0
    }

    client = NineRouterClient()
    answer = client.answer_financial_question("berapa pengeluaran bulan ini?", summary_data)
    assert answer is not None
    assert "Rp 550.000" in answer


@patch("app.sheets.client.SheetsClient.fetch_categories")
@patch("app.sheets.client.SheetsClient.fetch_accounts")
@patch("app.sheets.client.SheetsClient.append_transaction")
def test_sync_command_handler(mock_append, mock_accounts, mock_cats):
    """Test /sync command execution with mocked SheetsClient."""
    import asyncio
    from unittest.mock import AsyncMock
    from app.bot.handlers import sync_command

    mock_cats.return_value = []
    mock_accounts.return_value = []

    async def run_test():
        update = MagicMock()
        context = MagicMock()
        user = MagicMock()
        user.id = 123456789
        user.username = "danil2guna"
        update.effective_user = user
        update.message.reply_text = AsyncMock()

        await sync_command(update, context)
        update.message.reply_text.assert_called()

    asyncio.run(run_test())

