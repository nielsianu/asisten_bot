import sqlite3
import os
from pathlib import Path
from app.config.settings import settings


def get_db_connection() -> sqlite3.Connection:
    """Create and return a connection to the SQLite database."""
    db_path = Path(settings.database_path)
    os.makedirs(db_path.parent, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables for local caching and backup."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Transactions cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            type TEXT NOT NULL,
            business TEXT NOT NULL,
            category TEXT NOT NULL,
            account TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            source TEXT DEFAULT 'Telegram',
            ai_confidence INTEGER DEFAULT 100,
            synced_to_sheet INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Accounts cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            account_name TEXT NOT NULL,
            type TEXT NOT NULL,
            initial_balance REAL DEFAULT 0,
            current_balance REAL DEFAULT 0,
            notes TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    # Categories cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            business TEXT NOT NULL,
            type TEXT NOT NULL,
            category_name TEXT NOT NULL,
            keywords TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()
