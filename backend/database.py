import sqlite3
import os
from datetime import datetime
from config import SQLITE_PATH


def init_db():
    """Create the competitors table if it doesn't exist."""
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            last_updated TEXT,
            total_chunks INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def add_competitor(name, total_chunks):
    """Insert a new competitor or update an existing one."""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO competitors (name, last_updated, total_chunks)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            last_updated = excluded.last_updated,
            total_chunks = excluded.total_chunks
    """, (name, now, total_chunks))
    conn.commit()
    conn.close()


def get_all_competitors():
    """Return every tracked competitor as a list of dicts."""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, last_updated, total_chunks FROM competitors")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"name": r[0], "last_updated": r[1], "total_chunks": r[2]}
        for r in rows
    ]


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully")