# Personal Finance Telegram Bot - Roadmap

## Phase 1: MVP (Core Infrastructure & Sheet Connection)
- [x] Project setup & environment configuration loading (`.env`, `config/`).
- [x] Google Sheets integration client (Read/Write to `Settings`, `Accounts`, `Categories`, `Transactions`, `Budget`, `Dashboard`).
- [x] Local SQLite Cache setup for offline/backup & fast lookup.
- [x] Telegram Bot basic handlers (auth middleware, `/start`, `/help`, `/status`).
- [x] Automated Google Sheets Setup Script (`scripts/init_sheet.py`).

## Phase 2: Rule-based & Regex Parser Engine
- [x] Multi-layer Parser Pipeline Architecture (Rule -> Regex -> Synonym -> AI).
- [x] Rule Parser implementation (exact format match, explicit keyword commands).
- [x] Regex Parser implementation (nominal numbers, units e.g., `250rb`, `1.5jt`, account names, date detection).
- [x] Category & Account synonym lookup from Google Sheets cached tokens.
- [x] Transaction Confirmation UI (Telegram Inline Keyboards for confidence < 90%).
- [x] Undo, Edit, Delete transaction commands.

## Phase 3: Financial Dashboard & Reporting
- [x] Sheet-driven financial summary calculator service (Account balances, Monthly Income, Expense, Cash Flow).
- [x] Household vs. Catering business financial segregation reports.
- [x] Catering Profit & Loss calculation.
- [x] Telegram command summaries (`/rekap`, `/saldo`, `/top`).

## Phase 4: AI Enhancement (9Router Integration)
- [x] 9Router OpenAI-compatible client wrapper.
- [x] Natural Language Ambiguous Parser fallback (Structured JSON output parsing & validation).
- [x] Natural Language Query Engine & Structured Fallback Parser.
- [x] Smart Insights & monthly expense trend generation.
