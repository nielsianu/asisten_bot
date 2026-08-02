# Personal Finance Telegram Bot (`asisten_bot`)

A lightweight, reliable, and intelligent Telegram bot for managing personal finance and business catering expenses. Built with Python 3.11+, Google Sheets as the primary source of truth, SQLite for caching, and 9Router AI as a fallback natural language parser.

---

## 📌 Features

- **Multi-Business Support**: Separate tracking for **Household** (Rumah Tangga) and **Catering** (Usaha Katering).
- **Google Sheets Source of Truth**: All transactions, accounts, categories, and budgets are synced to Google Sheets.
- **Layered Parsing Strategy**:
  1. **Rule Engine**: Explicit structured commands (`/add ...`).
  2. **Regex Parser**: Quick natural language processing (e.g. `beli beras 250rb pakai blu`).
  3. **Synonym/Dictionary Lookup**: Mapping user terms to defined categories/accounts.
  4. **9Router AI Fallback**: LLM fallback for highly ambiguous natural language input.
- **Transaction Actions**: Confirmation workflow, Undo, Edit, and Delete support via Telegram inline buttons.
- **Financial Summaries & Insights**: Account balances, cash flow, top expenses, and catering net profit calculation.

---

## 📂 Project Architecture

```text
asisten_bot/
├── app/
│   ├── bot/          # Telegram Bot handlers, filters, and UI components
│   ├── parser/       # Multi-layered parser engine (Rule, Regex, Synonym, AI)
│   ├── ai/           # 9Router LLM client & structured JSON output prompt templates
│   ├── sheets/       # Google Sheets API client & batch synchronizer
│   ├── database/     # SQLite local cache & backup database repository
│   ├── services/     # Business logic, financial aggregations, undo manager
│   ├── models/       # Pydantic data schemas (Transaction, Account, Category)
│   ├── config/       # Pydantic Settings & environment loader
│   └── utils/        # Logger, date formatters, currency helpers
├── tests/            # Pytest test suite (Unit, Integration, Mocks)
├── docs/             # Technical specifications & documentation
├── logs/             # Application log output directory
├── data/             # SQLite local database directory
├── .env              # Secrets and configuration (Ignored in Git)
├── .env.example      # Template for environment configuration
├── asisten_bot_PRD.md # Product Requirements Document
├── ROADMAP.md        # Feature roadmap & phase planning
├── TASK.md           # Granular development task tracker
└── CHANGELOG.md      # Record of changes per version
```

---

## 🚀 Setup & Installation

### 1. Requirements
- Python 3.11+
- Google Cloud Service Account (with Google Sheets API enabled)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- 9Router API Key (OpenAI-compatible server)

### 2. Environment Configuration
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in the required values:
   - `TELEGRAM_BOT_TOKEN`: Token obtained from Telegram @BotFather.
   - `TELEGRAM_ALLOWED_USERS`: Your Telegram numeric ID (e.g., `123456789`).
   - `GOOGLE_SHEET_ID`: The ID of your Google Sheet.
   - `GOOGLE_CREDENTIALS_FILE`: Path to your Service Account JSON file (e.g., `credentials.json`).
   - `NINEROUTER_API_KEY`: API key for 9Router LLM Proxy.
   - `NINEROUTER_BASE_URL`: Base URL for 9Router endpoint (default: `http://localhost:8000/v1`).

### 3. Placing Google Credentials JSON
Place your Google Cloud Service Account credentials file in the project root directory as `credentials.json` (or set custom path in `GOOGLE_CREDENTIALS_FILE` inside `.env`).

---

## 🧪 Testing

Run pytest suite:
```bash
pytest
```

---

## 📤 Push to GitHub

To quickly push your updates to a public/private GitHub repository (with automatic credential protection):
- Double click **`push.bat`** (or run `.\push.bat` in CMD / PowerShell).

