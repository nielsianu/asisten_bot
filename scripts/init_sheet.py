"""
Google Sheets Initialization Script for Personal Finance Telegram Bot (asisten_bot)

This script connects to Google Sheets via Service Account credentials
and automatically creates & formats the required 6 tabs:
1. Settings
2. Accounts
3. Categories
4. Transactions
5. Budget
6. Dashboard
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()


def check_prerequisites():
    """Verify credentials file and SHEET_ID exist."""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: File '{CREDENTIALS_FILE}' tidak ditemukan di root directory!")
        print("   Silakan taruh file Service Account JSON dari Google Cloud Console di lokasi tersebut.")
        return False

    if not SHEET_ID:
        print("⚠️ Warning: GOOGLE_SHEET_ID di file .env masih kosong.")
        print("   Silakan buat Google Sheet baru di browser, lalu copy ID Sheet dari URL-nya ke .env.")
        print("   Contoh URL: https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit")
        return False

    return True


def initialize_sheets():
    """Setup worksheets, headers, and seed data."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("❌ Error: Library `gspread` atau `google-auth` belum terinstall.")
        print("   Jalankan: pip install gspread google-auth python-dotenv")
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)

    print(f"[INFO] Menghubungkan ke Google Sheet ID: {SHEET_ID}...")
    sh = gc.open_by_key(SHEET_ID)

    # 1. Settings Tab
    print("📝 Menyiapkan Tab 'Settings'...")
    try:
        ws_settings = sh.worksheet("Settings")
    except gspread.WorksheetNotFound:
        ws_settings = sh.add_worksheet(title="Settings", rows=100, cols=10)

    settings_headers = ["Key", "Value", "Description"]
    settings_data = [
        ["Bot Name", "Asisten Keuangan Bot", "Nama bot"],
        ["Currency", "IDR", "Mata uang utama"],
        ["Timezone", "Asia/Jakarta", "Zona waktu transaksi"],
        ["Default Household Account", "Cash", "Akun default transaksi rumah tangga"],
        ["Default Business Type", "Household", "Bisnis default (Household / Catering)"],
        ["AI Confidence Threshold", "90", "Threshold auto-confirm transaksi (%)"]
    ]
    ws_settings.clear()
    ws_settings.update(range_name="A1", values=[settings_headers] + settings_data)

    # 2. Accounts Tab
    print("💳 Menyiapkan Tab 'Accounts'...")
    try:
        ws_accounts = sh.worksheet("Accounts")
    except gspread.WorksheetNotFound:
        ws_accounts = sh.add_worksheet(title="Accounts", rows=100, cols=10)

    accounts_headers = ["ID", "Account Name", "Type", "Initial Balance", "Current Balance", "Notes", "Active"]
    accounts_data = [
        ["ACC-001", "Cash", "Cash", 0, "=Initial Balance", "Uang tunai fisik", "TRUE"],
        ["ACC-002", "Blu BCA", "Bank", 0, "=Initial Balance", "Rekening Blu BCA", "TRUE"],
        ["ACC-003", "BCA", "Bank", 0, "=Initial Balance", "Rekening Utama BCA", "TRUE"],
        ["ACC-004", "Mandiri", "Bank", 0, "=Initial Balance", "Rekening Mandiri", "TRUE"],
        ["ACC-005", "QRIS", "E-Wallet", 0, "=Initial Balance", "Saldo QRIS", "TRUE"],
        ["ACC-006", "E-Wallet", "E-Wallet", 0, "=Initial Balance", "GoPay/OVO/ShopeePay", "TRUE"]
    ]
    ws_accounts.clear()
    ws_accounts.update(range_name="A1", values=[accounts_headers] + accounts_data)

    # 3. Categories Tab
    print("🏷️ Menyiapkan Tab 'Categories'...")
    try:
        ws_categories = sh.worksheet("Categories")
    except gspread.WorksheetNotFound:
        ws_categories = sh.add_worksheet(title="Categories", rows=100, cols=10)

    categories_headers = ["ID", "Business", "Type", "Category Name", "Keywords", "Active"]
    categories_data = [
        # Household Expense
        ["CAT-001", "Household", "Expense", "Belanja Dapur", "beras, sayur, minyak, bumbu, daging, telur, ayam, ikan, udang, cabai, cabe, bawang, tepung, tahu, tempe, buah, lauk, belanja dapur, sembako", "TRUE"],
        ["CAT-002", "Household", "Expense", "Tagihan", "listrik, air, wifi, pulsa, token", "TRUE"],
        ["CAT-003", "Household", "Expense", "Transport", "bensin, parkir, tol, ojol, grab, gojek", "TRUE"],
        ["CAT-004", "Household", "Expense", "Jajan", "kopi, cemilan, es krim, boba, jajan", "TRUE"],
        ["CAT-005", "Household", "Expense", "Hiburan", "nonton, bioskop, game, netflix, spotify", "TRUE"],
        ["CAT-006", "Household", "Expense", "Kesehatan", "obat, dokter, vitamin, apotek", "TRUE"],
        ["CAT-007", "Household", "Expense", "Pendidikan", "buku, kursus, spp, sekolah", "TRUE"],
        ["CAT-008", "Household", "Expense", "Rumah Tangga", "sabun, detergen, perkakas, perlengkapan", "TRUE"],
        ["CAT-009", "Household", "Expense", "Lainnya", "misc, pengeluaran lain", "TRUE"],
        # Household Income
        ["CAT-010", "Household", "Income", "Gaji", "gaji, payroll, salary", "TRUE"],
        ["CAT-011", "Household", "Income", "Bonus", "thr, bonus, insentif", "TRUE"],
        ["CAT-012", "Household", "Income", "Lainnya", "pemasukan lain, transferan", "TRUE"],
        # Catering Income & Expense
        ["CAT-050", "Catering", "Income", "Penjualan", "pesanan, katering, nasi box, catering, order, menerima, pembayaran, pelunasan, tagihan, dp, lunas, bayaran, omset, penjualan, transferan, masuk", "TRUE"],
        ["CAT-051", "Catering", "Expense", "Bahan Baku", "sayur, ayam, daging, bumbu, beras, telur, ikan, udang, cabai, cabe, bawang, minyak, tepung, tahu, tempe, buah, bahan, lauk, belanja, sembako, bahan baku", "TRUE"],
        ["CAT-052", "Catering", "Expense", "Kemasan", "box, mika, plastik, sendok, sterofoam, dus, kemasan", "TRUE"],
        ["CAT-053", "Catering", "Expense", "Gas", "elpiji, gas 3kg, gas 12kg, gas", "TRUE"],
        ["CAT-054", "Catering", "Expense", "Transport", "ongkir katering, kurir, antar pesanan", "TRUE"],
        ["CAT-055", "Catering", "Expense", "Peralatan", "wajan, panci, pisau, alat masak", "TRUE"],
        ["CAT-056", "Catering", "Expense", "Marketing", "brosur, iklan, promosi, ig ads", "TRUE"],
        ["CAT-057", "Catering", "Expense", "Lainnya", "biaya operasional katering lain", "TRUE"],
    ]
    ws_categories.clear()
    ws_categories.update(range_name="A1", values=[categories_headers] + categories_data)

    # 4. Transactions Tab
    print("📊 Menyiapkan Tab 'Transactions'...")
    try:
        ws_transactions = sh.worksheet("Transactions")
    except gspread.WorksheetNotFound:
        ws_transactions = sh.add_worksheet(title="Transactions", rows=1000, cols=15)

    tx_headers = [
        "ID", "Date", "Time", "Type", "Business", 
        "Category", "Account", "Amount", "Description", 
        "Source", "AI Confidence"
    ]
    ws_transactions.clear()
    ws_transactions.update(range_name="A1", values=[tx_headers])

    # 5. Budget Tab
    print("🎯 Menyiapkan Tab 'Budget'...")
    try:
        ws_budget = sh.worksheet("Budget")
    except gspread.WorksheetNotFound:
        ws_budget = sh.add_worksheet(title="Budget", rows=100, cols=10)

    budget_headers = ["Category", "Business", "Monthly Budget", "Notes"]
    budget_data = [
        ["Belanja Dapur", "Household", 2000000, "Anggaran belanja bulanan"],
        ["Tagihan", "Household", 1000000, "Listrik, Air, Internet"],
        ["Transport", "Household", 500000, "Bensin & Transportasi"],
        ["Jajan", "Household", 500000, "Batas jajan per bulan"],
    ]
    ws_budget.clear()
    ws_budget.update(range_name="A1", values=[budget_headers] + budget_data)

    # 6. Dashboard Tab
    print("📈 Menyiapkan Tab 'Dashboard'...")
    try:
        ws_dashboard = sh.worksheet("Dashboard")
    except gspread.WorksheetNotFound:
        ws_dashboard = sh.add_worksheet(title="Dashboard", rows=100, cols=10)

    dashboard_data = [
        ["FINANCIAL DASHBOARD SUMMARY", "", ""],
        ["Metric", "Value", "Notes"],
        ["Total Income (Bulan Ini)", "=SUMIFS(Transactions!H:H, Transactions!D:D, \"Income\")", "Pemasukan"],
        ["Total Expense (Bulan Ini)", "=SUMIFS(Transactions!H:H, Transactions!D:D, \"Expense\")", "Pengeluaran"],
        ["Net Cash Flow", "=B3-B4", "Pemasukan - Pengeluaran"],
        ["", "", ""],
        ["CATERING BUSINESS SUMMARY", "", ""],
        ["Catering Income", "=SUMIFS(Transactions!H:H, Transactions!E:E, \"Catering\", Transactions!D:D, \"Income\")", "Omset Katering"],
        ["Catering Expense", "=SUMIFS(Transactions!H:H, Transactions!E:E, \"Catering\", Transactions!D:D, \"Expense\")", "Modal/Biaya Katering"],
        ["Catering Net Profit", "=B8-B9", "Laba Bersih Katering"]
    ]
    ws_dashboard.clear()
    ws_dashboard.update(range_name="A1", values=dashboard_data)

    # Delete default 'Sheet1' if exists and not needed
    try:
        sheet1 = sh.worksheet("Sheet1")
        if len(sh.worksheets()) > 1:
            sh.del_worksheet(sheet1)
    except gspread.WorksheetNotFound:
        pass

    print("✅ Inisialisasi Google Sheet BERHASIL!")
    print("🎉 Seluruh 6 tab (Settings, Accounts, Categories, Transactions, Budget, Dashboard) telah siap digunakan.")


if __name__ == "__main__":
    if check_prerequisites():
        initialize_sheets()
