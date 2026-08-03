import os
import pytest
from unittest.mock import patch, MagicMock
from app.models.transaction import Transaction
from app.services.report_service import ReportService
from app.database.connection import init_db
from app.config.settings import settings


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_file = tmp_path / "test_report.db"
    original_db = settings.database_path
    settings.database_path = str(db_file)
    init_db()
    yield
    settings.database_path = original_db


@patch("app.services.report_service.ReportService.get_all_transactions")
def test_generate_transaction_report(mock_get_txs):
    """Test text table report generation for /report command."""
    mock_get_txs.return_value = [
        Transaction(id="TX-001", date="2026-06-01", time="10:00", type="Expense", business="Household", category="Belanja Dapur", account="Cash", amount=150000, description="Beli sayuran komplit"),
        Transaction(id="TX-002", date="2026-06-05", time="14:00", type="Income", business="Catering", category="Penjualan", account="BCA", amount=2500000, description="DP Katering Pernikahan")
    ]

    chunks = ReportService.generate_transaction_report("2026-06")

    assert len(chunks) >= 1
    full_report = "".join(chunks)

    assert "LAPORAN TRANSAKSI" in full_report
    assert "JUNI 2026" in full_report
    assert "Date" in full_report
    assert "Description" in full_report
    assert "Amount (Rp)" in full_report
    assert "2026-06-01" in full_report
    assert "150.000" in full_report
    assert "2.500.000" in full_report


@patch("app.services.report_service.ReportService.get_all_transactions")
def test_generate_monthly_chart(mock_get_txs, tmp_path):
    """Test monthly bar chart generation for /chart command."""
    chart_file = tmp_path / "test_chart.png"
    mock_get_txs.return_value = [
        Transaction(id="TX-001", date="2026-05-10", time="10:00", type="Expense", business="Household", category="Belanja Dapur", account="Cash", amount=300000, description="Sembako"),
        Transaction(id="TX-002", date="2026-05-15", time="12:00", type="Income", business="Household", category="Gaji", account="BCA", amount=5000000, description="Gaji Bulanan"),
        Transaction(id="TX-003", date="2026-06-01", time="10:00", type="Expense", business="Catering", category="Bahan Baku", account="BCA", amount=1200000, description="Ayam & Daging"),
        Transaction(id="TX-004", date="2026-06-10", time="15:00", type="Income", business="Catering", category="Penjualan", account="BCA", amount=4000000, description="Order Katering")
    ]

    result_path = ReportService.generate_monthly_chart(output_path=str(chart_file))

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0


@patch("app.services.report_service.ReportService.get_all_transactions")
def test_generate_annual_pdf_report(mock_get_txs, tmp_path):
    """Test PDF annual report generation for /pdf command."""
    pdf_file = tmp_path / "test_annual_report.pdf"
    mock_get_txs.return_value = [
        Transaction(id="TX-001", date="2026-01-10", time="10:00", type="Expense", business="Household", category="Belanja Dapur", account="Cash", amount=500000, description="Beli Sayuran"),
        Transaction(id="TX-002", date="2026-02-15", time="12:00", type="Income", business="Catering", category="Penjualan", account="BCA", amount=8000000, description="Pesanan Catering"),
        Transaction(id="TX-003", date="2026-03-01", time="10:00", type="Expense", business="Catering", category="Bahan Baku", account="BCA", amount=3000000, description="Belanja Bahan Baku")
    ]

    result_path = ReportService.generate_annual_pdf_report("2026", output_path=str(pdf_file))

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0
