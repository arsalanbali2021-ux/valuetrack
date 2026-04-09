<p align="center">
  <img src="assets/logo.svg" alt="ValueTrack" width="72" height="72">
</p>

<h1 align="center">ValueTrack</h1>

<p align="center">
  A personal finance and insurance helper: track loans, watch your monthly spending, and find a health plan that actually fits your budget.
</p>

---

## What is this?

ValueTrack is a full-stack web app I built as my 2nd-year B.Tech mini project. It started as "let me just calculate an EMI properly" and kept growing. Now it covers four things:

- **Loans and EMIs.** Enter a loan and get the full month-by-month amortization schedule. Every rupee is calculated with `Decimal`, and the last month is adjusted so the balance lands exactly on ₹0.00.
- **Expenses.** Log what you spend, mark fixed costs (rent, subscriptions), set a monthly budget and see how close you are to it.
- **Insurance matching.** Give your age, budget and what you need covered (critical illness, maternity, accident). The scorer ranks every plan in the database and keeps the top 5, with a reason shown for each one.
- **Dashboard.** One screen with the numbers that matter: outstanding loan balance, next EMI, this month's spending against your budget, your best insurance match, plus charts.

There's also an **admin panel**. Admins can manage insurance plans, expense categories and system settings, and see the user list.

If you want the story of how it works under the hood, read [HOW_IT_WORKS.md](HOW_IT_WORKS.md). For the step-by-step request flow, read [FLOW.md](FLOW.md).

## Tech stack

| Layer    | What I used                                                  |
|----------|--------------------------------------------------------------|
| Frontend | HTML, CSS, vanilla JavaScript (Fetch API), Material Symbols  |
| Backend  | Python 3, Flask, Flask-CORS, SQLAlchemy 2, bcrypt            |
| Database | MySQL 8 (InnoDB, mostly 3NF)                                 |
| Testing  | pytest                                                       |

No React, no build step, no Docker. You clone it, point it at MySQL and run one Python file.

## Project structure

```
ValueTrack/
├── backend/
│   ├── app.py               # Flask app factory, registers blueprints, serves the frontend
│   ├── config.py            # reads .env (DB credentials, secret key)
│   ├── db.py                # SQLAlchemy engine + scoped session
│   ├── models.py            # ORM models for all tables
│   ├── routes/              # auth, loans, expenses, insurance, dashboard, admin
│   ├── services/            # the actual logic (EMI math, scoring, auth)
│   ├── tests/               # pytest tests
│   ├── requirements.txt
│   ├── .env.example
│   └── run.bat              # Windows shortcut to start the server
├── frontend/
│   ├── index.html           # login / register
│   ├── dashboard.html
│   ├── loans.html
│   ├── expenses.html
│   ├── insurance.html
│   ├── admin.html
│   ├── css/styles.css
│   └── js/                  # api.js wraps every backend call
├── database/
│   ├── schema.sql           # CREATE DATABASE + all tables
│   ├── seed_insurance.sql   # sample insurance plans
│   ├── seed_sample_users.sql
│   └── README_db.md
├── docs/                    # API docs, setup notes, assumptions, roadmap
├── assets/logo.svg
├── FLOW.md
├── HOW_IT_WORKS.md
└── PROJECT_DATABASE_Explanation.docx   # long-form database write-up (ER, normalization, viva Q&A)
```

## Getting started

### 1. What you need

- Python 3.10 or newer
- MySQL 8.0 or newer, running locally
- Git

### 2. Clone the repo

```bash
git clone https://github.com/arsalanbali2021-ux/valuetrack.git
cd valuetrack
```

### 3. Set up the database

```bash
mysql -u root -p < database/schema.sql
```

This creates the `valuetrack` database and all its tables. Before you seed anything, read the note under [Known issues](#known-issues). The current seed file is behind the schema.

### 4. Set up the backend

```bash
cd backend
python -m venv venv
```

Activate the virtual environment.

Windows:

```bash
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 5. Configure your environment

Copy the example env file:

```bash
cp .env.example .env
```

(On Windows Command Prompt use `copy .env.example .env`.)

Open `.env` and fill in your MySQL password. Change `SECRET_KEY` to any random string:

```
SECRET_KEY=some-long-random-string
FLASK_DEBUG=1
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=valuetrack
```

### 6. Run it

```bash
python app.py
```

Or just double-click `run.bat` on Windows.

Then open **http://127.0.0.1:5000** in your browser. Flask serves the frontend itself, so you don't need a second server. Register an account, log in, and you're in.

Quick check that the API is alive:

```bash
curl http://127.0.0.1:5000/api/health
```

### 7. Make yourself an admin (optional)

Nobody can sign up as an admin. That's on purpose. Register normally, then promote your account in MySQL:

```sql
USE valuetrack;
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

Log out and log back in. You'll land on the admin panel instead of the dashboard.

## Running the tests

```bash
cd backend
python -m pytest -v
```

The EMI tests (`test_emi.py`) run without a database. They check the formula, the zero-interest case and that the final balance is exactly zero.

## API at a glance

All endpoints live under `/api`. Responses look like `{ "status": "success", "message": "...", "data": {...} }`.

| Method | Endpoint                              | What it does                                  |
|--------|---------------------------------------|-----------------------------------------------|
| GET    | `/health`                             | Health check                                  |
| POST   | `/auth/register`                      | Create an account                             |
| POST   | `/auth/login`                         | Log in, returns user info and a token         |
| PUT    | `/auth/budget`                        | Save your monthly budget                      |
| POST   | `/loans`                              | Create a loan and generate its EMI schedule   |
| GET    | `/loans/<loan_id>/schedule`           | Get the full EMI schedule for a loan          |
| POST   | `/expenses`                           | Add an expense                                |
| GET    | `/expenses?user_id=&month=&year=`     | List expenses (optionally for one month)      |
| POST   | `/insurance/request`                  | Score all plans, save and return the top 5    |
| GET    | `/insurance/result/<request_id>`      | Fetch a saved ranking                         |
| GET    | `/dashboard?user_id=`                 | Everything the dashboard needs in one call    |
| GET/POST/PUT/DELETE | `/admin/insurance[/<id>]`  | Manage insurance plans (admin only)           |
| GET/POST/PUT/DELETE | `/admin/categories[/<id>]` | Manage expense categories (admin only)        |
| GET/PUT | `/admin/settings`                    | Read / update system settings (admin only)    |
| GET    | `/admin/users`                        | List users (admin only)                       |

More detail, including request bodies, is in [docs/API_DOCS.md](docs/API_DOCS.md). Some older notes there still mention the CSV import I later removed.

## Known issues

I'd rather list these than have you discover them at 2 a.m. before a demo.

- **Schema vs. models drift.** The Python models have a `users.monthly_budget` column and an `expenses.is_fixed` column, but `database/schema.sql` doesn't create them yet. Until that's fixed, run this after `schema.sql`:

  ```sql
  USE valuetrack;
  ALTER TABLE users    ADD COLUMN monthly_budget DECIMAL(12,2) DEFAULT 0.00;
  ALTER TABLE expenses ADD COLUMN is_fixed TINYINT(1) DEFAULT 0;
  ```

- **Insurance seed file is outdated.** `seed_insurance.sql` still uses the old columns (`provider_name`, `premium`, `pre_existing_allowed`). That was before I reworked insurance around critical illness, maternity and accident cover, so it won't insert into the current table. For now the easiest way to add plans is the admin panel.
- **Insurance tests are outdated too.** `test_insurance_scoring.py` still calls the old scorer signature, so those 4 tests fail. The EMI tests pass.
- **Auth is demo-grade.** Passwords are properly bcrypt-hashed, but after login the frontend keeps the user in `localStorage` and sends `user_id` with requests. The server doesn't verify the token on each call. It's fine for a college project on localhost. Don't put it on the internet like this.
- **Loans page has no "my loans" list.** You see a loan's schedule right after you create it, or by entering its ID.

## Where it's going

The wishlist is in [docs/ROADMAP.md](docs/ROADMAP.md). At the top: proper JWT auth, Alembic migrations (so the schema drift above can't happen again), a loans list, PDF export of EMI schedules, and EMI reminder emails.

## Docs

- [HOW_IT_WORKS.md](HOW_IT_WORKS.md): the walkthrough, in plain words
- [FLOW.md](FLOW.md): user flow and request flow, step by step
- [docs/SETUP.md](docs/SETUP.md): longer setup notes and troubleshooting
- [docs/API_DOCS.md](docs/API_DOCS.md): endpoint reference
- [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md): design decisions and defaults
- [database/README_db.md](database/README_db.md): table overview
- `PROJECT_DATABASE_Explanation.docx`: the full database write-up I used for my viva

## Author

**Arsalan Bali** ([@arsalanbali2021-ux](https://github.com/arsalanbali2021-ux))

If something breaks or doesn't make sense, open an issue. I'd genuinely like to know.
