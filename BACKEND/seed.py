"""
seed.py — Populate the database with demo customer accounts.

Run once from the terminal after the schema has been initialised:

    cd BACKEND
    python seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from werkzeug.security import generate_password_hash
from database import get_connection, init_db

DEMO_ACCOUNTS = [
    {"username": "alice",   "password": "password123", "name": "Alice Johnson",  "balance": 1000.00},
    {"username": "bob",     "password": "securepass",  "name": "Bob Williams",   "balance": 2500.00},
    {"username": "charlie", "password": "charlie99",   "name": "Charlie Brown",  "balance": 500.00},
]


def seed():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    for account in DEMO_ACCOUNTS:
        # Skip if the username already exists so re-running is safe.
        existing = cursor.execute(
            "SELECT id FROM customers WHERE username = ?", (account["username"],)
        ).fetchone()
        if existing:
            print(f"  [skip] {account['username']} already exists.")
            continue

        hashed = generate_password_hash(account["password"])
        cursor.execute(
            "INSERT INTO customers (username, password, name, balance) VALUES (?, ?, ?, ?)",
            (account["username"], hashed, account["name"], account["balance"]),
        )
        print(f"  [+] Created account for {account['name']} ({account['username']})")

    conn.commit()
    conn.close()
    print("Seeding complete.")


if __name__ == "__main__":
    seed()
