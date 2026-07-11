# Banking Web Application — Implementation Plan

> **Document Type:** Planning Only
> **Status:** Draft
> **Scope:** High-level architecture, component design, folder structure, module breakdown, and roadmap.
> This document does NOT contain database schema, SQL scripts, API contracts, or code-level details.

---

## 1. Solution Overview

### 1.1 Objective

Build a lightweight, browser-based banking web application that allows registered customers to securely log in, view their account balance, and perform basic financial transactions (deposit and withdrawal) through a clean, responsive interface.

### 1.2 Scope

| In Scope | Out of Scope |
|---|---|
| Customer login and session management | Admin or back-office portal |
| Dashboard with account summary | Multi-account support |
| View current balance | Inter-account transfers |
| Deposit funds | Interest calculation |
| Withdraw funds | Payment gateway integration |
| Logout and session termination | Mobile native app |

### 1.3 Users

| User Type | Description |
|---|---|
| **Customer** | Authenticated individual who owns a bank account and interacts with the application |

### 1.4 Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | A customer must be able to log in using a username and password |
| FR-02 | An authenticated customer must see a personalised dashboard upon login |
| FR-03 | A customer must be able to view their current account balance |
| FR-04 | A customer must be able to deposit a positive amount into their account |
| FR-05 | A customer must be able to withdraw an amount not exceeding their current balance |
| FR-06 | A customer must be able to log out, invalidating their session |
| FR-07 | Unauthenticated users must be redirected to the login page |

### 1.5 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | The UI must be responsive across desktop and mobile viewports (Bootstrap) |
| NFR-02 | Passwords must not be stored or transmitted in plaintext |
| NFR-03 | Session tokens must be invalidated on logout |
| NFR-04 | All state changes (deposit, withdrawal) must be persisted immediately |
| NFR-05 | The application must run on Python 3.11 |
| NFR-06 | The codebase must be testable via `pytest` |

### 1.6 Assumptions

- A pre-seeded set of customer accounts will exist in the database at startup.
- Only one account per customer is required.
- No email verification or password reset flow is needed for this scope.
- The application runs locally or on a single server; no horizontal scaling is required.
- SQLite is sufficient as the persistence layer for this workshop scope.

---

## 2. High-Level Architecture

### 2.1 Architecture Overview

The application follows a classic **three-tier architecture**:

```
┌─────────────────────────────────────────────────┐
│                  BROWSER (Client)                │
│         HTML pages rendered by Flask             │
│         Styled with Bootstrap 5                  │
└────────────────────┬────────────────────────────┘
                     │  HTTP Request / Response
                     ▼
┌─────────────────────────────────────────────────┐
│              BACKEND  (Flask / Python)           │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  Routes  │  │ Business │  │   Session    │   │
│  │ /login   │  │  Logic   │  │  Management  │   │
│  │ /dash    │  │ deposit/ │  │  (Flask)     │   │
│  │ /deposit │  │ withdraw │  │              │   │
│  │ /withdraw│  │ balance  │  │              │   │
│  │ /logout  │  └──────────┘  └──────────────┘   │
│  └──────────┘                                   │
└────────────────────┬────────────────────────────┘
                     │  SQL via sqlite3
                     ▼
┌─────────────────────────────────────────────────┐
│               DATABASE  (SQLite)                 │
│          Single-file, embedded database          │
│          Persists customers & transactions       │
└─────────────────────────────────────────────────┘
```

### 2.2 Frontend → Backend → Database Interaction

```
Browser                Flask Backend             SQLite DB
  │                        │                        │
  │── POST /login ─────────►                        │
  │                        │── query customer ──────►
  │                        │◄─ customer record ─────│
  │◄── redirect /dashboard─│                        │
  │                        │                        │
  │── GET /dashboard ──────►                        │
  │                        │── query balance ───────►
  │                        │◄─ balance data ─────────│
  │◄── render dashboard ───│                        │
  │                        │                        │
  │── POST /deposit ───────►                        │
  │                        │── update balance ──────►
  │                        │◄─ confirmation ─────────│
  │◄── redirect /dashboard─│                        │
```

### 2.3 Request Lifecycle

1. **Browser** sends an HTTP request (form submit or page navigation).
2. **Flask Router** matches the URL to a route handler function.
3. **Business Logic Layer** validates the request, applies rules (e.g. sufficient funds), and prepares the data operation.
4. **Database Layer** executes the read or write against the SQLite file.
5. **Flask** constructs an HTTP response — either a rendered HTML page (via Jinja2 template) or a redirect.
6. **Browser** displays the returned page.

---

## 3. Component Design

### 3.1 Frontend Responsibilities

| Concern | Approach |
|---|---|
| Page rendering | Jinja2 HTML templates served by Flask |
| Styling | Bootstrap 5 utility classes and components |
| Navigation | Bootstrap navbar with conditional login/logout links |
| Forms | HTML forms posting to Flask route endpoints |
| Feedback | Bootstrap alerts for success and error messages |
| Responsiveness | Bootstrap grid system for mobile-first layout |

The frontend has **no independent state** and **no JavaScript framework**. All logic lives in the backend; the browser is a pure view layer.

### 3.2 Backend Responsibilities

| Concern | Approach |
|---|---|
| Routing | Flask route decorators mapping URLs to handler functions |
| Authentication | Validate credentials; store user identity in Flask session |
| Session guard | Decorator / check to redirect unauthenticated requests |
| Business rules | Enforce non-negative deposits and sufficient-balance withdrawals |
| Data access | Read/write via Python `sqlite3` module |
| Template rendering | `render_template()` passing context variables to HTML |
| Configuration | App secret key and DB path from environment or config file |

### 3.3 Database Responsibilities

| Concern | Approach |
|---|---|
| Persistence | Single SQLite `.db` file stored inside the BACKEND folder |
| Customer data | Store account holder credentials and current balance |
| Transaction log | Record each deposit and withdrawal with amount and timestamp |
| Integrity | Enforce constraints at the database level |
| Seeding | A startup script or initialisation function populates demo accounts |

---

## 4. Folder Structure

```
banking-workshop/
│
├── FRONTEND/                   # All browser-facing assets
│   └── templates/              # Jinja2 HTML templates
│       ├── base.html           # Shared layout: navbar, Bootstrap CDN link
│       ├── login.html          # Login form page
│       ├── dashboard.html      # Account summary and action buttons
│       ├── deposit.html        # Deposit form page
│       └── withdraw.html       # Withdrawal form page
│
├── BACKEND/                    # All server-side code and data
│   ├── app.py                  # Flask application entry point; registers routes
│   ├── routes.py               # Route handlers (login, dashboard, deposit, etc.)
│   ├── auth.py                 # Authentication helpers and session utilities
│   ├── database.py             # DB connection, initialisation, and query helpers
│   ├── models.py               # Data access functions (get balance, update balance)
│   ├── banking.db              # SQLite database file (git-ignored)
│   └── seed.py                 # One-time script to populate demo accounts
│
├── tests/                      # Automated tests
│   ├── test_auth.py            # Tests for login and logout flows
│   ├── test_transactions.py    # Tests for deposit and withdrawal logic
│   └── conftest.py             # pytest fixtures (test app, test DB)
│
├── requirements.txt            # Python dependencies (flask, werkzeug, pytest)
├── .gitignore                  # Excludes banking.db, venv/, __pycache__/
└── IMPLEMENTATION_PLAN.md      # This document
```

### Folder Responsibilities

| Folder / File | Responsibility |
|---|---|
| `FRONTEND/templates/` | All rendered HTML; no logic, only presentation and form wiring |
| `BACKEND/app.py` | Application factory; Flask instance creation and blueprint registration |
| `BACKEND/routes.py` | URL-to-function mapping; thin handlers that call business logic |
| `BACKEND/auth.py` | Password verification, session read/write helpers, login-required guard |
| `BACKEND/database.py` | Connection management, schema initialisation, raw query execution |
| `BACKEND/models.py` | High-level data operations: fetch customer, update balance, log transaction |
| `BACKEND/seed.py` | Populate initial demo customer accounts for testing and demo purposes |
| `tests/` | Isolated unit and integration tests; use an in-memory SQLite test database |

---

## 5. Module Breakdown

### 5.1 Authentication Module

**Purpose:** Control who can access the application.

| Responsibility | Detail |
|---|---|
| Login | Accept username + password; verify against stored (hashed) credentials |
| Session creation | Store authenticated customer identity in Flask session cookie |
| Login guard | Protect all non-login routes; redirect unauthenticated requests to `/login` |
| Logout | Clear the session and redirect to login page |

**Key interactions:** Browser form → `/login` route → `auth.py` → `database.py`

---

### 5.2 Dashboard Module

**Purpose:** Provide the customer with an overview of their account after login.

| Responsibility | Detail |
|---|---|
| Identity display | Show customer name from session |
| Balance display | Fetch and render current balance from database |
| Navigation | Links/buttons to deposit, withdraw, and logout actions |

**Key interactions:** `/dashboard` route → `models.py` (get balance) → `dashboard.html`

---

### 5.3 Account Management Module

**Purpose:** Maintain the accuracy of customer account data.

| Responsibility | Detail |
|---|---|
| Balance retrieval | Query current balance for the logged-in customer |
| Balance update | Atomically apply deposit or withdrawal to balance |
| Consistency | Ensure balance never goes negative |

**Key interactions:** `models.py` ↔ `database.py` ↔ SQLite

---

### 5.4 Transactions Module

**Purpose:** Handle the deposit and withdrawal workflows end-to-end.

| Responsibility | Detail |
|---|---|
| Deposit flow | Validate positive amount → update balance → record transaction → redirect |
| Withdrawal flow | Validate positive amount → check sufficient funds → update balance → record transaction → redirect |
| User feedback | Pass success or error flash messages back to the template |
| Audit trail | Write each transaction to a log table with timestamp and type |

**Key interactions:** Browser form → `/deposit` or `/withdraw` route → `models.py` → `database.py`

---

## 6. Implementation Roadmap

### Phase 1 — Foundation

**Goal:** Establish project skeleton, configuration, and working Flask application.

| Task | Dependency |
|---|---|
| Create `FRONTEND/` and `BACKEND/` folder structure | None |
| Initialise `requirements.txt` with `flask`, `werkzeug`, `pytest` | None |
| Create `BACKEND/app.py` with minimal Flask app | requirements.txt |
| Create `BACKEND/database.py` with connection helper and schema initialisation | app.py |
| Create `BACKEND/seed.py` to insert demo accounts | database.py |

**Effort:** Low — pure scaffolding with no business logic.

---

### Phase 2 — Authentication

**Goal:** Deliver a working login and logout flow with session protection.

| Task | Dependency |
|---|---|
| Create `FRONTEND/templates/base.html` and `login.html` | Phase 1 complete |
| Create `BACKEND/auth.py` with password check and session helpers | database.py |
| Implement `/login` (GET + POST) and `/logout` routes in `routes.py` | auth.py, login.html |
| Apply login-required guard to all protected routes | auth.py |

**Effort:** Medium — requires credential verification and session lifecycle management.

---

### Phase 3 — Dashboard and Balance

**Goal:** Allow logged-in customers to see their account summary.

| Task | Dependency |
|---|---|
| Create `FRONTEND/templates/dashboard.html` | Phase 2 complete |
| Create `BACKEND/models.py` with `get_balance()` function | database.py |
| Implement `/dashboard` route | models.py, dashboard.html |

**Effort:** Low — primarily read-only data display.

---

### Phase 4 — Transactions

**Goal:** Enable customers to deposit and withdraw funds.

| Task | Dependency |
|---|---|
| Create `deposit.html` and `withdraw.html` templates | Phase 3 complete |
| Add `update_balance()` and `log_transaction()` to `models.py` | database.py |
| Implement `/deposit` (GET + POST) route with validation | models.py, deposit.html |
| Implement `/withdraw` (GET + POST) route with validation | models.py, withdraw.html |
| Add flash messages for success and error feedback | routes.py, templates |

**Effort:** Medium — requires input validation, business rule enforcement, and error messaging.

---

### Phase 5 — Testing and Quality

**Goal:** Validate correctness of all modules with automated tests.

| Task | Dependency |
|---|---|
| Create `tests/conftest.py` with pytest fixtures and test DB | Phase 4 complete |
| Write `tests/test_auth.py` (login, bad credentials, logout, session guard) | conftest.py |
| Write `tests/test_transactions.py` (deposit, withdraw, overdraft rejection) | conftest.py |
| Verify all tests pass via `pytest` | All test files |

**Effort:** Medium — test coverage for happy path and key failure scenarios.

---

### Phase Dependency Summary

```
Phase 1 (Foundation)
    └── Phase 2 (Authentication)
            └── Phase 3 (Dashboard)
                    └── Phase 4 (Transactions)
                                └── Phase 5 (Testing)
```

Each phase is a hard dependency on the one before it. Phases must be implemented sequentially.
