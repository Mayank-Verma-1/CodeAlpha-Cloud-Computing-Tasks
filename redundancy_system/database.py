"""
database.py
------------
Simulates the "cloud database" for Task 1 (Data Redundancy Removal System).

Uses SQLite as a lightweight stand-in for a real cloud DB (MySQL/PostgreSQL/
DynamoDB, etc). The interface (insert / fetch_all / exists_by_hash) is what
matters -- swap this class out for a real cloud connector without touching
the validation logic in validator.py.
"""

import sqlite3
import json
import os
from datetime import datetime


class CloudDatabase:
    def __init__(self, db_path="cloud_data.db", reset=False):
        if reset and os.path.exists(db_path):
            os.remove(db_path)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                record_hash TEXT NOT NULL UNIQUE,
                block_key TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        # Index on hash -> O(1)-ish exact duplicate lookup
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hash ON records(record_hash)")
        # Index on block_key -> only compare against a small bucket of
        # records instead of the whole table (fuzzy-match efficiency)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_block ON records(block_key)")
        self.conn.commit()

    def exists_by_hash(self, record_hash: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM records WHERE record_hash = ? LIMIT 1", (record_hash,))
        return cur.fetchone() is not None

    def fetch_candidates(self, block_key: str):
        """Return only records sharing the same block_key (efficient fuzzy check)."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM records WHERE block_key = ?", (block_key,))
        return [dict(row) for row in cur.fetchall()]

    def fetch_all(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM records ORDER BY id")
        return [dict(row) for row in cur.fetchall()]

    def insert(self, record: dict, record_hash: str, block_key: str, status: str = "verified"):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO records (data, record_hash, block_key, status, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (json.dumps(record), record_hash, block_key, status, datetime.utcnow().isoformat()),
        )
        self.conn.commit()
        return cur.lastrowid

    def count(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM records")
        return cur.fetchone()[0]

    def close(self):
        self.conn.close()
