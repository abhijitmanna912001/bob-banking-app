"""
test_auth.py — Unit tests for login, logout, and session-guard behaviour.
"""


def login(client, username="testuser", password="testpass123"):
    """Helper: POST to /login and return the response."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


class TestLogin:
    def test_valid_credentials_redirect_to_dashboard(self, client):
        """A correct login should redirect to /dashboard."""
        resp = login(client)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_wrong_password_shows_login_page(self, client):
        """Wrong password returns the login page with an error."""
        resp = login(client, password="wrongpassword")
        assert resp.status_code == 200
        assert b"Invalid credentials" in resp.data

    def test_unknown_username_shows_login_page(self, client):
        """A username that does not exist returns the login page with an error."""
        resp = login(client, username="nobody", password="x")
        assert resp.status_code == 200
        assert b"Invalid credentials" in resp.data

    def test_blank_username_shows_error(self, client):
        """Submitting a blank username returns a validation error."""
        resp = login(client, username="", password="testpass123")
        assert resp.status_code == 200
        assert b"Username is required" in resp.data

    def test_blank_password_shows_error(self, client):
        """Submitting a blank password returns a validation error."""
        resp = login(client, username="testuser", password="")
        assert resp.status_code == 200
        assert b"Password is required" in resp.data


class TestSessionGuard:
    def test_unauthenticated_dashboard_redirects_to_login(self, client):
        """GET /dashboard without a session redirects to /login."""
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_unauthenticated_deposit_redirects_to_login(self, client):
        resp = client.get("/deposit", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_unauthenticated_withdraw_redirects_to_login(self, client):
        resp = client.get("/withdraw", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


class TestLogout:
    def test_logout_clears_session_and_redirects(self, client):
        """After logout, /dashboard must redirect back to /login."""
        # Log in first.
        login(client)
        # Logout.
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]
        # Verify the session is cleared by trying to reach the dashboard.
        resp2 = client.get("/dashboard", follow_redirects=False)
        assert resp2.status_code == 302
        assert "/login" in resp2.headers["Location"]
