"""
auth.py — Authentication helpers: password verification, session utilities,
          and the login-required route guard.
"""
from functools import wraps

from flask import redirect, session, url_for
from werkzeug.security import check_password_hash

# ── Session key constants ────────────────────────────────────────────────────
SESSION_USER_ID   = "user_id"
SESSION_USER_NAME = "user_name"


# ── Password helpers ─────────────────────────────────────────────────────────

def verify_password(plain_text: str, hashed: str) -> bool:
    """Return True if *plain_text* matches the stored *hashed* password."""
    return check_password_hash(hashed, plain_text)


# ── Session helpers ──────────────────────────────────────────────────────────

def login_user(customer: dict) -> None:
    """Write the customer identity into the Flask session after a successful login."""
    session[SESSION_USER_ID]   = customer["id"]
    session[SESSION_USER_NAME] = customer["name"]


def logout_user() -> None:
    """Clear the entire Flask session on logout."""
    session.clear()


def get_current_user_id():
    """Return the logged-in customer's ID, or None if not authenticated."""
    return session.get(SESSION_USER_ID)


def get_current_user_name():
    """Return the logged-in customer's display name, or None if not authenticated."""
    return session.get(SESSION_USER_NAME)


# ── Login-required decorator ─────────────────────────────────────────────────

def login_required(f):
    """
    Decorator that redirects unauthenticated requests to /login.

    Usage::

        @app.route("/dashboard")
        @login_required
        def dashboard():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if get_current_user_id() is None:
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)
    return decorated
