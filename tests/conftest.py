"""
conftest.py — pytest fixtures shared across all test modules.

Every test gets:
- ``app``        : a Flask test application configured with an in-memory SQLite DB.
- ``client``     : the Flask test client for that app.
- ``auth_client``: a helper that logs the client in as the test user.
"""
import sys
import os

# Add BACKEND/ to the path so tests can import application modules directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "BACKEND"))

import pytest
from werkzeug.security import generate_password_hash

import database
import models
from app import create_app

TEST_USER = {
    "username": "testuser",
    "password": "testpass123",
    "name": "Test User",
    "balance": 1000.00,
}


@pytest.fixture()
def app():
    """
    Create a Flask app configured for testing:
    - TESTING=True so Flask propagates exceptions.
    - DATABASE=:memory: so every test run starts fresh.
    """
    test_app = create_app(
        {
            "TESTING": True,
            "DATABASE": ":memory:",
            "SECRET_KEY": "test-secret-key",
        }
    )

    # Seed the in-memory DB with known test data.
    conn = database.get_connection(":memory:")
    with test_app.app_context():
        # get_connection() inside models uses the default DB_PATH, but during
        # tests we patch the db_path via monkeypatching below.
        pass

    yield test_app


@pytest.fixture()
def client(app):
    """Return the Flask test client."""
    with app.test_client() as c:
        # Seed a fresh in-memory DB for each test so state doesn't leak.
        _seed_test_db(app)
        yield c


def _seed_test_db(app):
    """
    Initialise the schema and insert the test user into the in-memory DB.

    Because the app uses a shared in-memory database at DATABASE=':memory:',
    we patch models and database to point at the same connection each time.
    """
    import database as db_module

    # Patch the DB_PATH used by the database module to ":memory:" path.
    # SQLite's ":memory:" creates a *new* DB per connection, so we need a
    # file-based temp DB instead to share state across functions.
    import tempfile
    tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmpfile.close()
    tmp_path = tmpfile.name

    # Patch DB_PATH so all module-level helpers use this temp file.
    db_module.DB_PATH = tmp_path
    app.config["DATABASE"] = tmp_path

    db_module.init_db(tmp_path)

    conn = db_module.get_connection(tmp_path)
    cursor = conn.cursor()
    # Remove any leftover rows from a previous fixture call.
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM transactions")
    cursor.execute(
        "INSERT INTO customers (username, password, name, balance) VALUES (?, ?, ?, ?)",
        (
            TEST_USER["username"],
            generate_password_hash(TEST_USER["password"]),
            TEST_USER["name"],
            TEST_USER["balance"],
        ),
    )
    conn.commit()
    conn.close()
