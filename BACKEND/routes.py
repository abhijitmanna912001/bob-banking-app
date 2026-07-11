"""
routes.py — All Flask route handlers.

Each handler is thin: it validates input, delegates to models/auth helpers,
and returns a response.  No SQL is written directly here.
"""
import sys
import os

# Allow importing sibling modules when routes.py is imported by app.py
sys.path.insert(0, os.path.dirname(__file__))

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

import models
from auth import (
    get_current_user_id,
    get_current_user_name,
    login_required,
    login_user,
    logout_user,
    verify_password,
)

bp = Blueprint("main", __name__)

MAX_TRANSACTION = 1_000_000.00


# ── /login ───────────────────────────────────────────────────────────────────────────

@bp.route("/login", methods=["GET", "POST"])
def login():
    # Already authenticated — skip the login page.
    if get_current_user_id() is not None:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Basic field presence checks
        if not username:
            flash("Username is required.", "error")
            return render_template("login.html")
        if not password:
            flash("Password is required.", "error")
            return render_template("login.html")

        customer = models.get_customer_by_username(username)

        # Use a single generic message to prevent username enumeration.
        if customer is None or not verify_password(password, customer["password"]):
            flash("Invalid credentials. Please try again.", "error")
            return render_template("login.html")

        login_user(dict(customer))
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


# ── /logout ──────────────────────────────────────────────────────────────────────────

@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.login"))


# ── /dashboard ─────────────────────────────────────────────────────────────────────

@bp.route("/dashboard")
@login_required
def dashboard():
    customer_id = get_current_user_id()
    balance = models.get_balance(customer_id)
    return render_template(
        "dashboard.html",
        customer_name=get_current_user_name(),
        balance=balance,
    )


# ── /deposit ─────────────────────────────────────────────────────────────────────────

@bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "POST":
        raw_amount = request.form.get("amount", "").strip()

        if not raw_amount:
            flash("Amount is required.", "error")
            return render_template("deposit.html")

        try:
            amount = float(raw_amount)
        except ValueError:
            flash("Amount must be a number.", "error")
            return render_template("deposit.html")

        if amount <= 0:
            flash("Amount must be greater than zero.", "error")
            return render_template("deposit.html")

        if amount > MAX_TRANSACTION:
            flash("Amount exceeds the maximum deposit limit of £1,000,000.", "error")
            return render_template("deposit.html")

        customer_id = get_current_user_id()
        current_balance = models.get_balance(customer_id)
        new_balance = round(current_balance + amount, 2)

        models.update_balance(customer_id, new_balance)
        models.log_transaction(customer_id, "deposit", amount)

        flash(f"£{amount:,.2f} deposited successfully. New balance: £{new_balance:,.2f}", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("deposit.html")


# ── /withdraw ────────────────────────────────────────────────────────────────────────

@bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    if request.method == "POST":
        raw_amount = request.form.get("amount", "").strip()

        if not raw_amount:
            flash("Amount is required.", "error")
            return render_template("withdraw.html")

        try:
            amount = float(raw_amount)
        except ValueError:
            flash("Amount must be a number.", "error")
            return render_template("withdraw.html")

        if amount <= 0:
            flash("Amount must be greater than zero.", "error")
            return render_template("withdraw.html")

        if amount > MAX_TRANSACTION:
            flash("Amount exceeds the maximum withdrawal limit of £1,000,000.", "error")
            return render_template("withdraw.html")

        customer_id = get_current_user_id()

        # Atomically deduct the amount only if balance is sufficient.
        # This single UPDATE prevents the TOCTOU race condition where two
        # concurrent requests could both pass a Python-level balance check
        # and both commit, resulting in a negative balance (overdraft).
        success = models.withdraw_atomic(customer_id, amount)
        if not success:
            flash("Insufficient funds.", "error")
            return render_template("withdraw.html")

        new_balance = models.get_balance(customer_id)
        models.log_transaction(customer_id, "withdrawal", amount)

        flash(f"£{amount:,.2f} withdrawn successfully. New balance: £{new_balance:,.2f}", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("withdraw.html")
