"""
test_transactions.py — Integration tests for deposit and withdrawal flows.

Each test logs in as the seed user before performing the transaction.
"""


def login(client):
    client.post(
        "/login",
        data={"username": "testuser", "password": "testpass123"},
        follow_redirects=True,
    )


def get_balance_from_dashboard(client) -> float:
    """Parse the current balance out of the dashboard page."""
    resp = client.get("/dashboard", follow_redirects=True)
    html = resp.data.decode()
    # The balance is rendered as £X,XXX.XX — extract the numeric part.
    import re
    match = re.search(r"£([\d,]+\.\d{2})", html)
    if match:
        return float(match.group(1).replace(",", ""))
    raise AssertionError(f"Could not find balance on dashboard. HTML snippet:\n{html[:500]}")


class TestDeposit:
    def test_valid_deposit_increases_balance(self, client):
        login(client)
        resp = client.post(
            "/deposit",
            data={"amount": "200"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        balance = get_balance_from_dashboard(client)
        assert balance == 1200.00

    def test_deposit_zero_shows_error(self, client):
        login(client)
        resp = client.post(
            "/deposit",
            data={"amount": "0"},
            follow_redirects=True,
        )
        assert b"greater than zero" in resp.data
        assert get_balance_from_dashboard(client) == 1000.00

    def test_deposit_negative_shows_error(self, client):
        login(client)
        resp = client.post(
            "/deposit",
            data={"amount": "-50"},
            follow_redirects=True,
        )
        assert b"greater than zero" in resp.data
        assert get_balance_from_dashboard(client) == 1000.00

    def test_deposit_non_numeric_shows_error(self, client):
        login(client)
        resp = client.post(
            "/deposit",
            data={"amount": "abc"},
            follow_redirects=True,
        )
        assert b"must be a number" in resp.data

    def test_deposit_empty_amount_shows_error(self, client):
        login(client)
        resp = client.post(
            "/deposit",
            data={"amount": ""},
            follow_redirects=True,
        )
        assert b"Amount is required" in resp.data


class TestWithdrawal:
    def test_valid_withdrawal_decreases_balance(self, client):
        login(client)
        resp = client.post(
            "/withdraw",
            data={"amount": "300"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        balance = get_balance_from_dashboard(client)
        assert balance == 700.00

    def test_overdraft_shows_insufficient_funds(self, client):
        login(client)
        resp = client.post(
            "/withdraw",
            data={"amount": "9999"},
            follow_redirects=True,
        )
        assert b"Insufficient funds" in resp.data
        assert get_balance_from_dashboard(client) == 1000.00

    def test_withdraw_zero_shows_error(self, client):
        login(client)
        resp = client.post(
            "/withdraw",
            data={"amount": "0"},
            follow_redirects=True,
        )
        assert b"greater than zero" in resp.data
        assert get_balance_from_dashboard(client) == 1000.00

    def test_withdraw_negative_shows_error(self, client):
        login(client)
        resp = client.post(
            "/withdraw",
            data={"amount": "-100"},
            follow_redirects=True,
        )
        assert b"greater than zero" in resp.data

    def test_withdraw_empty_amount_shows_error(self, client):
        login(client)
        resp = client.post(
            "/withdraw",
            data={"amount": ""},
            follow_redirects=True,
        )
        assert b"Amount is required" in resp.data

    def test_exact_balance_withdrawal_succeeds(self, client):
        """Withdrawing exactly the full balance must succeed."""
        login(client)
        resp = client.post(
            "/withdraw",
            data={"amount": "1000"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert get_balance_from_dashboard(client) == 0.00
