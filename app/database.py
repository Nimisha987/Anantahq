"""SQLite connection handling and schema."""
import sqlite3
from collections.abc import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    code            TEXT PRIMARY KEY,           -- case-sensitive
    original_url    TEXT    NOT NULL,
    created_at      TEXT    NOT NULL,           -- ISO-8601, UTC
    expires_at      TEXT,                       -- ISO-8601, UTC, NULL = never
    click_count     INTEGER NOT NULL DEFAULT 0,
    last_clicked_at TEXT
);
"""

def connect(db_path:str)->sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory= sqlite3.Row
    return conn

def init_db(db_path:str)->None:
    conn = connect(db_path)

    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()

def connection_scope(db_path:str)->Iterator[sqlite3.Connection]:
    """One connection per request, always closed afterwards."""
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()