"""
app.py — Flask application entry point.

Start the app from the BACKEND/ directory:

    FLASK_APP=app.py FLASK_ENV=development flask run
"""
import os
import sys

# Ensure sibling modules (database, routes, models, auth) are importable
# regardless of which directory the process is started from.
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask

from database import init_db
from routes import bp as main_bp

# ── Application factory ──────────────────────────────────────────────────────

def create_app(test_config=None):
    """
    Create and configure the Flask application.

    *test_config* is a dict of configuration values used by the test suite to
    override production defaults (e.g. point at an in-memory SQLite DB).
    """
    templates_dir = os.path.join(
        os.path.dirname(__file__), "..", "FRONTEND", "templates"
    )

    app = Flask(__name__, template_folder=templates_dir)

    # ── Default configuration ────────────────────────────────────────────────
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production"),
        DATABASE=os.path.join(os.path.dirname(__file__), "banking.db"),
        DEBUG=True,
    )

    if test_config is not None:
        app.config.update(test_config)

    # ── Schema initialisation ────────────────────────────────────────────────
    db_path = app.config.get("DATABASE")
    with app.app_context():
        init_db(db_path if db_path != ":memory:" else db_path)

    # ── Register blueprints ──────────────────────────────────────────────────
    app.register_blueprint(main_bp)

    # ── Custom error handlers ────────────────────────────────────────────────
    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        from flask import render_template
        return render_template("500.html"), 500

    # ── Root redirect ────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("main.login"))

    return app


# ── Entry point ──────────────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
