"""
database.py — SQLite connection, schema initialisation, and query helpers.
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "banking.db")


def get_connection(db_path=None):
    """Open and return a sqlite3 connection with dict-like row access."""
    path = db_path if db_path is not None else DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None):
    """Create the customers and transactions tables if they do not exist."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            name     TEXT    NOT NULL,
            balance  REAL    NOT NULL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id      INTEGER NOT NULL,
            transaction_type TEXT    NOT NULL,
            amount           REAL    NOT NULL,
            created_at       TEXT    NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        """
    )
    conn.commit()
    conn.close()


def query(sql, params=(), db_path=None, fetchone=False):
    """
    Execute *sql* with *params* and return results.

    For SELECT statements, returns a list of sqlite3.Row objects (or a single
    Row when fetchone=True).  For INSERT/UPDATE/DELETE, returns None and
    commits automatically.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    is_select = sql.strip().upper().startswith("SELECT")
    if is_select:
        result = cursor.fetchone() if fetchone else cursor.fetchall()
    else:
        conn.commit()
        result = None
    conn.close()
    return result
