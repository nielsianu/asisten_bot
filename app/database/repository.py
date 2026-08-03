import sqlite3
from typing import List, Optional
from app.database.connection import get_db_connection
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category


class TransactionRepository:
    """Local SQLite cache repository for transactions."""

    @staticmethod
    def save_transaction(tx: Transaction, synced: bool = True):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO transactions 
            (id, date, time, type, business, category, account, amount, description, source, ai_confidence, synced_to_sheet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tx.id, tx.date, tx.time, tx.type, tx.business, tx.category,
            tx.account, tx.amount, tx.description, tx.source, tx.ai_confidence,
            1 if synced else 0
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def sync_transactions_from_sheet(txs: List[Transaction]):
        """Mirror transactions fetched from Google Sheets into local SQLite repository.
        Preserves any unsynced local offline transactions.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        for tx in txs:
            cursor.execute("""
                INSERT OR REPLACE INTO transactions 
                (id, date, time, type, business, category, account, amount, description, source, ai_confidence, synced_to_sheet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                tx.id, tx.date, tx.time, tx.type, tx.business, tx.category,
                tx.account, tx.amount, tx.description, tx.source, tx.ai_confidence
            ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_recent_transactions(limit: int = 10) -> List[Transaction]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, date, time, type, business, category, account, amount, description, source, ai_confidence
            FROM transactions
            ORDER BY date DESC, time DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [Transaction(**dict(row)) for row in rows]

    @staticmethod
    def get_unsynced_transactions() -> List[Transaction]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, date, time, type, business, category, account, amount, description, source, ai_confidence
            FROM transactions
            WHERE synced_to_sheet = 0
            ORDER BY created_at ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [Transaction(**dict(row)) for row in rows]

    @staticmethod
    def mark_as_synced(tx_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE transactions SET synced_to_sheet = 1 WHERE id = ?", (tx_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_transaction(tx_id: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0


class CacheRepository:
    """Repository for caching Accounts and Categories locally."""

    @staticmethod
    def cache_accounts(accounts: List[Account]):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts")
        for acc in accounts:
            cursor.execute("""
                INSERT INTO accounts (id, account_name, type, initial_balance, current_balance, notes, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (acc.id, acc.account_name, acc.type, acc.initial_balance, acc.current_balance, acc.notes, 1 if acc.active else 0))
        conn.commit()
        conn.close()

    @staticmethod
    def get_cached_accounts() -> List[Account]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE active = 1")
        rows = cursor.fetchall()
        conn.close()
        return [
            Account(
                id=r["id"],
                account_name=r["account_name"],
                type=r["type"],
                initial_balance=r["initial_balance"],
                current_balance=r["current_balance"],
                notes=r["notes"],
                active=bool(r["active"])
            ) for r in rows
        ]

    @staticmethod
    def cache_categories(categories: List[Category]):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories")
        for cat in categories:
            keywords_str = ", ".join(cat.keywords)
            cursor.execute("""
                INSERT INTO categories (id, business, type, category_name, keywords, active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cat.id, cat.business, cat.type, cat.category_name, keywords_str, 1 if cat.active else 0))
        conn.commit()
        conn.close()

    @staticmethod
    def get_cached_categories() -> List[Category]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE active = 1")
        rows = cursor.fetchall()
        conn.close()
        return [
            Category.from_raw_keywords(
                id=r["id"],
                business=r["business"],
                type=r["type"],
                category_name=r["category_name"],
                keywords_str=r["keywords"] or "",
                active=bool(r["active"])
            ) for r in rows
        ]
