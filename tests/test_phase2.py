import pytest
from app.parser.rule import RuleParser
from app.parser.regex import RegexParser
from app.parser.synonym import SynonymParser
from app.parser.pipeline import ParserPipeline
from app.services.transaction_service import TransactionService
from app.database.connection import init_db
from app.config.settings import settings


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_file = tmp_path / "test_phase2.db"
    original_db = settings.database_path
    settings.database_path = str(db_file)
    init_db()
    yield
    settings.database_path = original_db


def test_rule_parser():
    """Test explicit rule parser matching."""
    res = RuleParser.parse("/add expense 25000 jajan cash kopi sore")
    assert res.success is True
    assert res.type == "Expense"
    assert res.amount == 25000.0
    assert res.category == "Jajan"
    assert res.account == "Cash"
    assert res.confidence == 100

    invalid = RuleParser.parse("random text 123")
    assert invalid.success is False


def test_regex_parser():
    """Test nominal extraction and account detection."""
    res1 = RegexParser.parse("beli beras 250rb pakai blu")
    assert res1.success is True
    assert res1.amount == 250000.0
    assert res1.account == "Blu BCA"
    assert res1.business == "Household"
    assert res1.type == "Expense"

    res2 = RegexParser.parse("dapat omset katering 1.5jt ke bca")
    assert res2.success is True
    assert res2.amount == 1500000.0
    assert res2.account == "BCA"
    assert res2.business == "Catering"
    assert res2.type == "Income"

    res3 = RegexParser.parse("bayar listrik 500k mandiri")
    assert res3.success is True
    assert res3.amount == 500000.0
    assert res3.account == "Mandiri"


def test_synonym_enrichment():
    """Test category enrichment from keywords."""
    res = RegexParser.parse("beli beras 250rb pakai blu")
    enriched = SynonymParser.enrich(res)
    assert enriched.category == "Belanja Dapur"
    assert enriched.confidence >= 95

    # Catering Income test examples
    ex1 = ParserPipeline.parse("menerima pembayaran katering 90 ribu dari ibu Ayu")
    assert ex1.success is True
    assert ex1.type == "Income"
    assert ex1.business == "Catering"
    assert ex1.category == "Penjualan"
    assert ex1.amount == 90000.0

    ex2 = ParserPipeline.parse("Pelunasan tagihan katering dari Mama nida 50k")
    assert ex2.success is True
    assert ex2.type == "Income"
    assert ex2.business == "Catering"
    assert ex2.category == "Penjualan"
    assert ex2.amount == 50000.0

    ex3 = ParserPipeline.parse("pembayaran bu Ayu katering 72 ribu udah di transfer ke blu")
    assert ex3.success is True
    assert ex3.type == "Income"
    assert ex3.business == "Catering"
    assert ex3.category == "Penjualan"
    assert ex3.account == "Blu BCA"
    assert ex3.amount == 72000.0


    # Sayuran keyword test examples
    res_sayur1 = RegexParser.parse("beli sayuran 50rb pakai blu")
    enriched_sayur1 = SynonymParser.enrich(res_sayur1)
    assert enriched_sayur1.category == "Belanja Dapur"
    assert enriched_sayur1.business == "Household"

    res_sayur2 = RegexParser.parse("bayar sayuran katering 150k cash")
    enriched_sayur2 = SynonymParser.enrich(res_sayur2)
    assert enriched_sayur2.category == "Bahan Baku"
    assert enriched_sayur2.business == "Catering"


def test_parser_pipeline():
    """Test full multi-layer pipeline."""
    res = ParserPipeline.parse("beli sayur dan bumbu 50k cash")
    assert res.success is True
    assert res.amount == 5000.0 or res.amount == 50000.0
    assert res.category == "Belanja Dapur"
    assert res.account == "Cash"
    assert res.is_confident is True

    res2 = ParserPipeline.parse("beli sayuran 75rb blu")
    assert res2.success is True
    assert res2.amount == 75000.0
    assert res2.category == "Belanja Dapur"
    assert res2.account == "Blu BCA"


def test_transaction_service_and_undo():
    """Test saving and undoing transactions."""
    parsed = ParserPipeline.parse("beli beras 200rb cash")
    tx = TransactionService.create_from_parsed(parsed)

    # Undo
    ok_save, _ = TransactionService.save_transaction(tx)
    assert ok_save is True

    ok_undo, undo_msg = TransactionService.undo_last_transaction()
    assert ok_undo is True
    assert "dibatalkan" in undo_msg


def test_handle_callback_query():
    """Test inline callback query confirmation handler."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    import json
    from app.bot.handlers import handle_callback_query

    async def run_test():
        update = MagicMock()
        context = MagicMock()

        user = MagicMock()
        user.id = 123456789
        user.username = "danil2guna"
        update.effective_user = user

        query = AsyncMock()
        query.data = "confirm_tx"
        update.callback_query = query

        context.user_data = {
            "pending_tx": json.dumps({
                "t": "Expense", "b": "Household", "c": "Jajan",
                "a": "Cash", "m": 25000, "d": "Kopi", "cf": 80
            })
        }

        await handle_callback_query(update, context)

        # Verify message was edited successfully
        query.edit_message_text.assert_called_once()
        args, kwargs = query.edit_message_text.call_args
        assert "BERHASIL DISIMPAN" in args[0]

    asyncio.run(run_test())


def test_group_chat_message_filter():
    """Test group chat message filter logic."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    from app.bot.handlers import handle_text_message

    async def run_test():
        update = MagicMock()
        context = MagicMock()
        context.bot.username = "AsistenBot"
        context.bot.id = 99999

        user = MagicMock()
        user.id = 123456789
        user.username = "danil2guna"
        update.effective_user = user

        # Group chat general conversation (should be IGNORED)
        chat = MagicMock()
        chat.type = "group"
        update.effective_chat = chat
        update.message.text = "Nanti malam makan apa teman-teman?"
        update.message.reply_to_message = None
        update.message.reply_text = AsyncMock()

        await handle_text_message(update, context)

        # Ensure bot replied 0 times (ignored)
        update.message.reply_text.assert_not_called()

    asyncio.run(run_test())

