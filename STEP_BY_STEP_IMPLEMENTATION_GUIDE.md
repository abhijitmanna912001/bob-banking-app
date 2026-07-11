# Banking Web Application — Step-by-Step Implementation Guide

> **Document Type:** Implementation Instructions
> **Companion Document:** `IMPLEMENTATION_PLAN.md`
> **Language:** Plain English — logic and intent only, no raw code listings.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 Create the Project Folder Structure

Start by creating two top-level folders at the root of the workspace:

- `FRONTEND/` — will hold all HTML templates.
- `BACKEND/` — will hold all Python source files and the SQLite database.
- `tests/` — will hold all automated test files.

Inside `FRONTEND/`, create a sub-folder called `templates/`. Flask looks for HTML templates inside a folder named `templates`, so the structure must match exactly.

### 1.2 Set Up a Python Virtual Environment

A virtual environment isolates the project's Python packages from the rest of the system. The steps are:

1. Navigate to the project root in a terminal.
2. Create a new virtual environment using Python 3.11. This creates a hidden folder (commonly named `venv`) that contains its own Python interpreter and package manager.
3. Activate the virtual environment. On macOS/Linux this is done by sourcing a shell script inside the `venv/bin/` folder. On Windows the activation script is inside `venv\Scripts\`.
4. Once activated, your terminal prompt changes to indicate you are inside the virtual environment. All `pip install` commands from this point forward install packages only into this environment.

> Keep the virtual environment active for every terminal session while developing or running the application.

### 1.3 Install Dependencies

Create a file called `requirements.txt` at the project root and list the three required packages, one per line:

- `flask` — the web framework.
- `werkzeug` — Flask's underlying utility library; used directly for password hashing.
- `pytest` — the test runner.

Then install all three in one command by pointing `pip` at the `requirements.txt` file. This ensures everyone working on the project installs identical versions.

### 1.4 Verify Flask Is Working

After installation, confirm Flask is correctly installed by asking it to print its version from the command line. If it responds with a version number, the environment is ready.

### 1.5 Configure `.gitignore`

Before any code is written, add the following patterns to `.gitignore` so they are never accidentally committed:

- `venv/` — the virtual environment folder.
- `__pycache__/` — Python's compiled bytecode cache.
- `*.pyc` — individual compiled Python files.
- `BACKEND/banking.db` — the SQLite database file (contains live customer data).

---

## 2. Backend Implementation

### 2.1 Database Initialisation (`database.py`)

This file is responsible for everything related to the SQLite connection. It should do three things:

**Connection helper:** Write a function that opens and returns a connection to the `banking.db` file located inside the `BACKEND/` folder. The connection should be configured to return rows as dictionary-like objects so field values can be accessed by column name rather than by index position.

**Schema initialisation:** Write a second function that creates the two required tables if they do not already exist — one for customer accounts (holding the username, hashed password, full name, and balance) and one for the transaction log (holding a reference to the customer, the transaction type, the amount, and a timestamp). Call this function once at application startup.

**Query helper (optional):** A small utility that executes any SQL statement and returns the result, handling the connection open/close lifecycle automatically. This avoids repeating boilerplate in every other file.

### 2.2 Demo Account Seeding (`seed.py`)

This is a standalone script, not imported by the application. Its only purpose is to populate the database with a handful of realistic demo accounts so the application can be demonstrated without a registration flow.

The logic is:
1. Open a connection to the database (call the helper from `database.py`).
2. For each demo customer, hash their plain-text password using Werkzeug's `generate_password_hash()` function before storing it. Never store plain text.
3. Insert the customer record with a starting balance (e.g. £1,000).
4. Close the connection.

Run this script once from the terminal after `app.py` has initialised the schema.

### 2.3 Application Entry Point (`app.py`)

This file creates and configures the Flask application instance. It should:

1. Import Flask and create the `app` object.
2. Set a **secret key** on the app. Flask uses this to cryptographically sign session cookies. Use a long, random string. For local development this can be hardcoded; for production it should be read from an environment variable.
3. Tell Flask where to find HTML templates. Because the templates live in `FRONTEND/templates/` rather than the default `templates/` folder, pass the correct path when creating the `app` object using the `template_folder` parameter.
4. Call the database schema initialisation function so tables are created on first startup.
5. Register all the routes (either by importing `routes.py` or using Flask Blueprints).
6. At the bottom, add the standard `if __name__ == "__main__"` guard and call `app.run()` with `debug=True` for local development.

### 2.4 Authentication Helpers (`auth.py`)

This module contains reusable functions that the route handlers call. It should NOT contain any route definitions itself — only helper logic.

**Password verification:** Write a function that accepts a plain-text password and the stored hash, and returns `True` or `False` using Werkzeug's `check_password_hash()`. This keeps all password logic in one place.

**Login-required guard:** Write a function or decorator that checks whether the current Flask session contains a logged-in user. If the session does not have a `user_id` key (or equivalent), it immediately redirects the request to the login page. Wrap every protected route handler with this guard so unauthenticated visitors cannot reach the dashboard, deposit, or withdraw pages.

**Session helpers:** Write two small functions — one that writes the customer's ID and name into the session after a successful login, and one that clears the session entirely on logout. Centralising session key names in one file prevents bugs caused by typos scattered across multiple route files.

### 2.5 Route Handlers (`routes.py`)

Each route handler is responsible for exactly two things: calling the right business logic and returning the right response. Handlers should contain no database queries directly — delegate those to `models.py`.

**`GET /login`**
- If the user is already logged in (session is set), redirect them to the dashboard immediately.
- Otherwise, render `login.html` with no error message.

**`POST /login`**
- Read the username and password from the submitted form data.
- Call the model to look up the customer by username.
- If no customer is found, re-render the login page with a generic "Invalid credentials" message. Do not tell the user whether the username or the password was wrong — this prevents username enumeration.
- If the customer is found, call the password-verification helper. If it returns `False`, re-render the login page with the same generic error.
- If verification passes, call the session-write helper, then redirect to `/dashboard`.

**`GET /dashboard`**
- Apply the login-required guard.
- Read the customer ID from the session.
- Call `get_balance()` from `models.py` to fetch the current balance.
- Render `dashboard.html`, passing in the customer name and balance as template variables.

**`GET /deposit`**
- Apply the login-required guard.
- Render `deposit.html` with no pre-filled values.

**`POST /deposit`**
- Apply the login-required guard.
- Read the submitted amount from the form.
- Run validation (see Section 5).
- If validation fails, re-render `deposit.html` with the error message.
- If validation passes, call `update_balance()` and `log_transaction()` from `models.py`.
- Flash a success message and redirect to `/dashboard`.

**`GET /withdraw`**
- Apply the login-required guard.
- Render `withdraw.html` with no pre-filled values.

**`POST /withdraw`**
- Apply the login-required guard.
- Read the submitted amount from the form.
- Call `get_balance()` to check the current balance.
- Run validation (see Section 5).
- If validation fails, re-render `withdraw.html` with the error message.
- If validation passes, call `update_balance()` and `log_transaction()`.
- Flash a success message and redirect to `/dashboard`.

**`GET /logout`**
- Call the session-clear helper from `auth.py`.
- Redirect to `/login`.

### 2.6 Data Access Layer (`models.py`)

This file contains all functions that read from or write to the database. Route handlers call these functions; they never write SQL themselves.

**`get_customer_by_username(username)`**
- Queries the customers table for a row matching the given username.
- Returns the full customer record (as a dict) or `None` if not found.

**`get_balance(customer_id)`**
- Queries the customers table for the balance column of the given customer.
- Returns the balance as a number.

**`update_balance(customer_id, new_balance)`**
- Writes the new balance value back to the customers table for the given customer.
- This is a single UPDATE statement; the calling code is responsible for computing the new balance before calling this function.

**`log_transaction(customer_id, transaction_type, amount)`**
- Inserts a new row into the transactions table.
- The `transaction_type` is a string, either `"deposit"` or `"withdrawal"`.
- The timestamp is generated automatically (using SQLite's `CURRENT_TIMESTAMP` or Python's `datetime.now()`).

### 2.7 Session Management

Flask sessions work through a cryptographically signed cookie stored in the browser. The session behaves like a Python dictionary — you can read from and write to it using standard dictionary syntax.

Key rules to follow:
- Always store the minimum information needed in the session: the customer ID and display name are enough. Never store the password hash or the full customer record.
- Set the secret key to a value that is long and random. A short or predictable secret key makes the session signature breakable.
- When a user logs out, call `session.clear()` to remove all keys, not just the user-specific ones. This prevents partial session data from lingering.
- Flask sessions expire when the browser is closed by default. For this scope, that behaviour is acceptable.

### 2.8 Error Handling

Rather than letting Python exceptions propagate to the browser (which would show a raw stack trace), register two custom error handlers on the Flask app:

**404 handler:** Renders a simple "Page not found" HTML page when a URL does not match any route.

**500 handler:** Renders a simple "Something went wrong" HTML page for unhandled server errors. In development, Flask's built-in debugger is more useful, so only activate this handler when `debug=False`.

For user-facing validation errors (wrong password, insufficient funds), use Flask's `flash()` mechanism rather than exceptions. Flash messages are stored temporarily in the session and displayed once on the next page render.

---

## 3. Frontend Implementation

All HTML files live inside `FRONTEND/templates/`. Flask's `render_template()` function resolves template names relative to the configured `template_folder`, so no path prefixes are needed in the Python calls.

### 3.1 Base Layout (`base.html`)

This template defines the shared page chrome that every other page inherits. Using Jinja2's `extends` and `block` mechanism, child templates can inject their own content without duplicating the layout.

The base layout should contain:
- The HTML `<head>` section with the Bootstrap 5 CDN link (stylesheet and JS bundle) and a `<title>` block that child templates can override.
- A responsive Bootstrap **navbar** at the top with the bank's name on the left. On the right, show a "Logout" link if the user is logged in, or nothing if they are not. Use a Jinja2 conditional to check a `current_user` or similar variable passed from the route.
- A Bootstrap **container** in the body where a `content` block allows child templates to inject their page-specific HTML.
- A section at the top of the container that loops over Flask flash messages and renders each one as a Bootstrap alert (green for success, red for error). This ensures every page automatically shows feedback without extra work in each template.

### 3.2 Login Page (`login.html`)

Extends `base.html`. Contains a single, centred Bootstrap **card** with:
- A card header titled "Customer Login".
- A form with two fields: a text input for the username and a password input for the password.
- A "Login" submit button styled with Bootstrap's primary button class.
- The form's `action` attribute points to `/login` and the method is `POST`.
- No client-side validation — all checking is done on the server.

### 3.3 Dashboard (`dashboard.html`)

Extends `base.html`. Displays:
- A welcome heading that includes the customer's name (passed as a template variable from the route).
- An "Account Summary" Bootstrap **card** that shows the current balance, formatted as currency.
- Two Bootstrap **buttons** side by side: "Deposit Funds" linking to `/deposit` and "Withdraw Funds" linking to `/withdraw`.
- The balance value is a Jinja2 variable injected by the route handler; the template simply renders it.

### 3.4 Deposit Form (`deposit.html`)

Extends `base.html`. Contains:
- A heading "Deposit Funds".
- A Bootstrap card with a form containing one numeric input field labelled "Amount".
- The input should have `type="number"` and a `min` attribute of `0.01` so the browser provides a first line of defence against zero or negative amounts (the server validates again independently).
- A "Deposit" submit button.
- A "Back to Dashboard" link below the form.
- The form posts to `/deposit`.

### 3.5 Withdraw Form (`withdraw.html`)

Extends `base.html`. Mirrors the deposit form in structure, with:
- A heading "Withdraw Funds".
- The same single amount field.
- A "Withdraw" submit button.
- A "Back to Dashboard" link.
- The form posts to `/withdraw`.

### 3.6 Bootstrap Layout Principles

Apply these conventions consistently across all templates:

| Concern | Bootstrap Approach |
|---|---|
| Page width | Wrap all content in `container` or `container-md` |
| Centring cards | Use `row justify-content-center` + `col-md-5` |
| Spacing | Use margin/padding utilities (`mt-4`, `mb-3`, `p-3`) |
| Buttons | `btn btn-primary` for main action, `btn btn-secondary` for back links |
| Alerts | `alert alert-success` for confirmations, `alert alert-danger` for errors |
| Responsive text | Use Bootstrap's default typographic scale; no custom CSS is needed |

---

## 4. Integration Steps

### 4.1 Connect Flask to SQLite

The connection between Flask and SQLite is managed entirely in `database.py`. The integration works as follows:

1. **Path resolution:** The database file path is constructed relative to the `BACKEND/` folder using Python's `os.path` utilities. This makes the path work regardless of which directory the app is started from.
2. **Connection per request:** Open a connection at the start of each database operation and close it immediately after. For this scope, a single connection opened and closed per function call is simpler and safer than a persistent connection.
3. **Row factory:** Set the connection's `row_factory` to `sqlite3.Row`. This makes every query result behave like a dictionary, so templates and route handlers can access `row["balance"]` instead of `row[2]`.
4. **Schema on startup:** Call the schema initialisation function once inside `app.py` before the first request is processed. Flask provides a suitable hook for this (`with app.app_context()`).

### 4.2 Connect Frontend Templates to Backend Routes

The connection happens through HTML `<form>` elements and `<a>` links:

- Every form's `action` attribute must exactly match the Flask route URL (e.g. `action="/deposit"`).
- Every form's `method` must be `POST` for state-changing operations and `GET` for navigation.
- Links use standard `<a href="/dashboard">` — no AJAX, no JavaScript fetch calls.
- Template variables passed by `render_template()` are referenced in HTML using Jinja2's double-curly-brace syntax: `{{ variable_name }}`.
- Flash messages are accessed via Jinja2's `get_flashed_messages(with_categories=True)` call inside the base template loop.

### 4.3 Tell Flask Where the Templates Live

Because the templates folder is inside `FRONTEND/` rather than the default location, the Flask app must be told explicitly. When creating the Flask `app` object in `app.py`, pass the `template_folder` argument with the path to `FRONTEND/templates`. Use `os.path.join` with `os.path.dirname(__file__)` to construct an absolute path that works from any working directory.

---

## 5. Validation Rules

All validation is performed on the server side in the route handler, before any database operation. The frontend `min` attribute on number inputs is a convenience hint to the browser only and cannot be relied upon for security.

### 5.1 Login Validation

| Check | Condition | Error Response |
|---|---|---|
| Non-empty username | Username field is not blank | Re-render login with "Username is required" |
| Non-empty password | Password field is not blank | Re-render login with "Password is required" |
| Username exists | `get_customer_by_username()` returns a record | Re-render login with "Invalid credentials" |
| Password matches | `check_password_hash()` returns True | Re-render login with "Invalid credentials" |

> Always use the same generic error message ("Invalid credentials") for both "username not found" and "wrong password". A different message for each case would let an attacker enumerate which usernames are registered.

### 5.2 Balance Validation

The balance read from the database is the single source of truth. Before any withdrawal, the route handler must:

1. Fetch the current balance using `get_balance()`.
2. Compare it against the requested withdrawal amount.
3. Proceed only if the balance is strictly greater than or equal to the requested amount.

The balance must never go below zero. This rule is enforced in Python before writing to the database — do not rely on database constraints alone.

### 5.3 Deposit Checks

| Check | Condition | Error Response |
|---|---|---|
| Field is not empty | The amount field has a value | Flash "Amount is required" |
| Amount is a valid number | The value can be converted to a float without error | Flash "Amount must be a number" |
| Amount is positive | The converted value is greater than zero | Flash "Amount must be greater than zero" |
| Amount is reasonable | Optionally cap at a large maximum (e.g. £1,000,000 per transaction) | Flash "Amount exceeds maximum deposit limit" |

On success: new balance = current balance + deposit amount.

### 5.4 Withdrawal Checks

| Check | Condition | Error Response |
|---|---|---|
| Field is not empty | The amount field has a value | Flash "Amount is required" |
| Amount is a valid number | The value converts to float without error | Flash "Amount must be a number" |
| Amount is positive | Converted value is greater than zero | Flash "Amount must be greater than zero" |
| Sufficient funds | Current balance >= requested amount | Flash "Insufficient funds" |

On success: new balance = current balance − withdrawal amount.

---

## 6. Testing

### 6.1 Test Setup (`conftest.py`)

Before writing any tests, set up the shared test infrastructure in `tests/conftest.py`. This file is automatically loaded by `pytest` before any tests run.

**Test application fixture:** Create a version of the Flask app configured for testing. Key differences from the production app:
- Set `TESTING = True` on the app configuration. This causes Flask to propagate exceptions rather than handling them.
- Point the database at an **in-memory SQLite database** (`:memory:`) instead of `banking.db`. This means every test run starts with a completely empty, fresh database.
- Initialise the schema and insert a small set of known test accounts within the fixture. This gives tests predictable data to assert against.

**Test client fixture:** Flask provides a built-in test client that simulates HTTP requests without starting a real server. Create a fixture that returns this client for use in every test function.

### 6.2 Unit Tests (`test_auth.py`)

Unit tests target isolated, single-function behaviour. For authentication:

| Test Case | What to Assert |
|---|---|
| Valid login | POST to `/login` with correct credentials returns a redirect to `/dashboard` |
| Wrong password | POST with correct username but wrong password returns the login page with an error |
| Unknown username | POST with a username that does not exist returns the login page with an error |
| Logged-out access to dashboard | GET `/dashboard` without logging in returns a redirect to `/login` |
| Logout clears session | After login, GET `/logout` clears the session; subsequent GET `/dashboard` redirects to `/login` |

For each test, use the test client fixture to make the HTTP request and inspect the response status code and response body.

### 6.3 Integration Tests (`test_transactions.py`)

Integration tests exercise multiple components together. For transactions:

| Test Case | What to Assert |
|---|---|
| Successful deposit | POST a valid amount to `/deposit`; then GET `/dashboard` and confirm the displayed balance increased by that amount |
| Deposit of zero | POST an amount of zero; confirm the error flash message appears and the balance is unchanged |
| Deposit of negative amount | POST a negative number; confirm the error flash message appears |
| Successful withdrawal | POST a valid amount less than the balance; confirm balance decreased |
| Overdraft attempt | POST an amount greater than the current balance; confirm "Insufficient funds" flash message appears and balance is unchanged |
| Withdrawal of zero | POST zero; confirm the error flash message appears |

For each test, log in first using the test client (so the session is set), then perform the transaction action, then verify the outcome.

### 6.4 Manual Testing Checklist

Run through this checklist in the browser before considering any feature complete:

**Authentication**
- [ ] Visiting `/dashboard` without logging in redirects to `/login`.
- [ ] Submitting the login form with blank fields shows an error.
- [ ] Submitting with a wrong password shows a generic error (not "user not found").
- [ ] Submitting with correct credentials lands on the dashboard.
- [ ] Clicking Logout returns to the login page and the back button no longer shows the dashboard.

**Dashboard**
- [ ] The correct customer name is displayed after login.
- [ ] The balance shown matches the seeded starting balance.

**Deposit**
- [ ] Submitting the deposit form with a valid amount updates the balance on the dashboard.
- [ ] The success flash message appears after a valid deposit.
- [ ] Submitting zero or a negative amount shows an error and the balance does not change.

**Withdrawal**
- [ ] Submitting a valid amount reduces the balance correctly.
- [ ] The success flash message appears after a valid withdrawal.
- [ ] Submitting an amount greater than the balance shows "Insufficient funds".
- [ ] Submitting zero or a negative amount shows an error.

**Responsiveness**
- [ ] All pages are usable at 375px wide (mobile) using the browser's device emulator.
- [ ] The navbar collapses correctly on small viewports.

---

## 7. Deployment

### 7.1 Run the Application Locally

Follow these steps in order every time you start the application fresh:

1. Activate the virtual environment.
2. Navigate to the `BACKEND/` folder.
3. If this is the first run, execute `seed.py` to populate the database with demo accounts.
4. Set the `FLASK_APP` environment variable to point at `app.py`.
5. Optionally set `FLASK_ENV=development` to enable the interactive debugger and auto-reloader.
6. Run the Flask development server. By default it listens on `http://127.0.0.1:5000`.
7. Open a browser and navigate to `http://localhost:5000`. You should be redirected to the login page.

> The development server is single-threaded and not designed to handle concurrent users. It is for local testing only.

### 7.2 Running Tests

With the virtual environment active, run `pytest` from the project root. pytest will automatically discover all files named `test_*.py` inside the `tests/` folder. The output shows passed, failed, and skipped tests. All tests must pass before pushing code.

To see more detail (including `print()` output), run pytest with the `-v` (verbose) flag.

### 7.3 Production Considerations

The following changes are required before deploying to any environment accessible to real users:

| Concern | Development Approach | Production Requirement |
|---|---|---|
| WSGI server | Flask built-in dev server | Use Gunicorn or uWSGI; Flask's dev server is not production-safe |
| Secret key | Hardcoded string in `app.py` | Read from an environment variable; never commit to source control |
| Debug mode | `debug=True` | Set `debug=False`; the interactive debugger exposes the server to code execution attacks |
| Database | SQLite file | SQLite is acceptable for low-traffic single-server deployments; migrate to PostgreSQL for multi-user production |
| HTTPS | Not required locally | Mandatory in production; use a reverse proxy (Nginx) with a TLS certificate |
| Environment variables | Optional | Store secret key and DB path in environment variables or a `.env` file excluded from git |
| Logging | Console output | Configure Python's `logging` module to write to a file with rotation |

### 7.4 GitHub Actions CI/CD

A pre-configured workflow file already exists at `docs/demo-setup/banking-app-ci.yml`. Once copied to `.github/workflows/`, it will automatically:

1. Check out the code on every push to `main` or any `feature/**` branch.
2. Set up Python 3.11.
3. Install all dependencies from `requirements.txt`.
4. Run the full `pytest` suite.

The pipeline fails (blocking the merge) if any test fails. This ensures the main branch always contains passing code.

To activate the pipeline, copy or move `banking-app-ci.yml` into a `.github/workflows/` folder at the repository root.
