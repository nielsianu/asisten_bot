# CHANGELOG

## [Unreleased] - 2026-08-03

### Added
- **Google Sheets Primary Database Architecture**: Shifted read/write operations to live Google Sheets API as single source of truth with SQLite local backup cache.
- **Categorization & Grocery Enhancements**: Added `sayuran` and expanded grocery keywords to `Belanja Dapur` (Household) and `Bahan Baku` (Catering).
- **New Telegram Bot Commands (`/report`, `/chart`, `/pdf`, `/budget`)**:
  - `/report`: Generates formatted text table of monthly transactions.
  - `/chart`: Generates matplotlib bar chart of monthly expense (red) vs income (green).
  - `/pdf`: Generates ReportLab annual financial PDF report with executive summary, category subtotals, and 12-month breakdown.
  - `/budget`: Reads directly from Google Sheets `"Budget"` worksheet (`Category` and `Monthly Budget` columns) and maps Category sheet Column G `Budget` to compute remaining monthly budget in real time.
- **Automatic Telegram UI Command Menu Registration**: Added `post_init` in `main.py` calling `bot.set_my_commands()` to register slash menu autocomplete popup list in Telegram UI.
- Project workspace structure (`app/`, `tests/`, `docs/`, `logs/`, `data/`).
- Initial configuration files: `.env`, `.env.example`, `.gitignore`.
- Documentation: `ROADMAP.md`, `TASK.md`, `README.md`.
- Google Sheets Template Specification ([docs/GOOGLE_SHEET_TEMPLATE.md](file:///d:/PJ/antigravity/asisten_bot/docs/GOOGLE_SHEET_TEMPLATE.md)).
- Automated Google Sheets setup script ([scripts/init_sheet.py](file:///d:/PJ/antigravity/asisten_bot/scripts/init_sheet.py)).
- **Phase 1 Infrastructure**: Config loader (`app/config/settings.py`), Domain Models (`app/models/`), SQLite Database & Cache (`app/database/`), Google Sheets Client (`app/sheets/client.py`), Telegram Bot Core (`app/bot/`).
- **Phase 2 Multi-layer Parser & Confirmation Workflow**: Rule Engine (`app/parser/rule.py`), Regex Parser (`app/parser/regex.py`), Synonym Matcher (`app/parser/synonym.py`), Pipeline Engine (`app/parser/pipeline.py`), Transaction & Undo Service (`app/services/transaction_service.py`), Telegram Inline Confirmation Keyboards.
- **Phase 3 Dashboard & Summary Commands**: Aggregation engine (`app/services/dashboard_service.py`), Telegram commands `/saldo` & `/top`.
- **Phase 4 9Router AI Gateway & Natural Language Q&A**: OpenAI-compatible client wrapper (`app/ai/client.py`) for ambiguous natural language fallback parsing & natural language financial Q&A (e.g., "berapa pengeluaran bulan ini?").
- **9Router SSE Streaming & Model Optimization**: Added SSE stream parser (`data: ...`) to support 9Router streaming output and updated model configuration to high-performance `ag/gemini-3.6-flash-high`.
- **Google Sheets Automatic Cleaning & Bidirectional Sync**:
  - Implemented `overwrite_transactions()` in `SheetsClient` ([app/sheets/client.py](file:///d:/PJ/antigravity/asisten_bot/app/sheets/client.py#L117)).
  - `/sync` now purges leftover test dummy rows in Google Sheets `Transactions` tab and aligns it 1-to-1 with valid local SQLite transactions.
- **Telegram Group Chat & Mention Handler**: Added group chat filtering and automatic `@mention` tag stripping in `handle_text_message`. The bot ignores general group conversations and only responds to text messages in groups when tagged (e.g., `@sistim beli beras 250rb`) or replied to.
- **Catering Income & Expense Parser Enhancements**:
  - Added support for customer catering income & bill settlements (`menerima pembayaran`, `pelunasan tagihan`, `dp katering`, `pembayaran katering ... di transfer ke blu`) mapping to `Type: Income`, `Business: Catering`, `Category: Penjualan`.
  - Expanded `Bahan Baku` (Catering) and `Belanja Dapur` (Household) keywords (`sayur`, `ayam`, `daging`, `bumbu`, `beras`, `telur`, `ikan`, `udang`, `cabai`, `bawang`, `minyak`, `tepung`, `tahu`, `tempe`, `buah`, `lauk`, `belanja`).
- **Automated GitHub Deployment Script**: Created `push.bat` for double-click automated Git initialization, commit, and push to GitHub Public Repository with strict `.gitignore` credential masking.
- **Enhanced `/help` & `/rekap` Commands**:
  - `/help` now lists all available commands with usage examples.
  - `/rekap` now calculates total income, total expense, cash flow, and catering profit. Added flexible month & year parameters (e.g., `/rekap juni 2026`, `/rekap 2026-06`).
- **Dependencies Update**: Added `pydantic-settings>=2.0.0` to [requirements.txt](file:///d:/PJ/antigravity/asisten_bot/requirements.txt) to resolve `ModuleNotFoundError: No module named 'pydantic_settings'` on Linux server deployments.
- **Bugfix**: Fixed `NameError: name 'SheetsClient' is not defined` in `sync_command` by importing `SheetsClient` in [app/bot/handlers.py](file:///d:/PJ/antigravity/asisten_bot/app/bot/handlers.py). Added unit test `test_sync_command_handler` in [tests/test_phase3_4.py](file:///d:/PJ/antigravity/asisten_bot/tests/test_phase3_4.py).
- Comprehensive Unit & Integration Test suites ([tests/test_phase1.py](file:///d:/PJ/antigravity/asisten_bot/tests/test_phase1.py), [tests/test_phase2.py](file:///d:/PJ/antigravity/asisten_bot/tests/test_phase2.py), [tests/test_phase3_4.py](file:///d:/PJ/antigravity/asisten_bot/tests/test_phase3_4.py)) — 100% Passed (16/16 tests).
