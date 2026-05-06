<p align="center">
  <img src="assets/logo.svg" alt="ValueTrack" width="72" height="72">
</p>

<h1 align="center">ValueTrack</h1>

<p align="center">
  A personal finance and insurance helper: track loans, watch your monthly spending, and find a health plan that actually fits your budget.
</p>

<p align="center">
  <sub>🎓 College mini project · 2nd-year B.Tech</sub>
</p>

---

## What is this?

> **This is a college mini project.** I built ValueTrack in my 2nd year of B.Tech as my mini project. The database write-up I prepared for my viva is included in this repo too. It's built to show how the pieces of a real app fit together (database design, a layered backend, and a frontend that talks to an API). It isn't a production finance product, so please don't put real financial data in it.

ValueTrack is a full-stack web app. It started as "let me just calculate an EMI properly" and kept growing. Now it covers four things:

- **Loans and EMIs.** Enter a loan and get the full month-by-month amortization schedule. Every rupee is calculated with `Decimal`, and the last month is adjusted so the balance lands exactly on ₹0.00.
- **Expenses.** Log what you spend, mark fixed costs (rent, subscriptions), set a monthly budget and see how close you are to it.
- **Insurance matching.** Give your age, budget and what you need covered (critical illness, maternity, accident). The scorer ranks every plan in the database and keeps the top 5, with a reason shown for each one. You can also pick **"IRDAI-registered plans only"**, which ranks only plans linked to a real product from IRDAI's public register.
- **Dashboard.** One screen with the numbers that matter: outstanding loan balance, next EMI, this month's spending against your budget, your best insurance match, plus charts.

There's also an **admin panel**. Admins can manage insurance plans, expense categories and system settings, see the user list, and import the **IRDAI product catalogue** (more on that [below](#irdai-registered-recommendations)).

If you want the story of how it works under the hood, read [HOW_IT_WORKS.md](HOW_IT_WORKS.md). For the step-by-step request flow, read [FLOW.md](FLOW.md).

## What makes it different

There are plenty of EMI calculators and expense trackers out there. Here's what I think sets this one apart:

- **Loans, spending and insurance in one place.** Most apps do one of these. ValueTrack puts your EMIs, your monthly budget and your insurance choice side by side on one dashboard, because in real life they all come out of the same salary.
- **The whole EMI schedule, not just one number.** Most calculators stop at "your EMI is ₹10,258". ValueTrack shows every month: how much is interest, how much actually reduces the loan, and what's left.
- **Money math that adds up to the paisa.** Every calculation uses `Decimal` with bank-style rounding, and the last month is adjusted so the loan closes at exactly ₹0.00. No `-0.03` left over at the end.
- **Insurance recommendations that explain themselves.** You don't just get a score. Each plan comes with plain reasons like "Under budget: ₹900/mo" or "NO Maternity Cover", so you can see why it ranked where it did.
- **Built around what people actually ask.** The insurance filters are critical illness, maternity and accident cover, plus age and a monthly budget. Those are the questions families in India really ask when picking a health plan, rather than generic policy jargon.
- **Backed by the regulator's own list.** Plans can be linked to their official IRDAI UIN, the ID every approved product in India gets. Users can choose to see only IRDAI-registered plans, and each one shows its insurer, UIN and approval date.
- **Rules you can read, not a black box.** The scoring is plain rule-based logic with fixed weights, all in one file. Anyone can check it, question it, or change it.
- **Made for India.** Rupees everywhere, Indian-style loan amounts, and sample plans modelled on the kind of health covers sold here.
- **Runs with almost no setup.** One Flask server serves both the API and the pages. There's no build step, no Node and no Docker: just Python and MySQL.
- **An admin panel included.** Plans, categories and settings can be managed from the browser instead of editing the database by hand.

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
│   ├── services/            # the actual logic (EMI math, scoring, auth, IRDAI import)
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
│   ├── migrate_v1_1.sql     # upgrade for databases created before v1.1
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

This creates the `valuetrack` database and all its tables. Then load the sample data:

```bash
mysql -u root -p valuetrack < database/seed_insurance.sql
```

```bash
mysql -u root -p valuetrack < database/seed_sample_users.sql
```

The first gives the recommender 30 plans to rank. The second is optional and adds demo accounts so you can log in straight away:

| Email               | Password      | Role  |
|---------------------|---------------|-------|
| `alice@example.com` | `Password123` | user (budget ₹25,000) |
| `bob@example.com`   | `SecurePass1` | user  |
| `admin@example.com` | `AdminPass1`  | admin |

These are for local testing only.

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

Then open **http://127.0.0.1:5000** in your browser. Flask serves the frontend itself, so you don't need a second server. Log in with a demo account or register your own.

Quick check that the API is alive:

```bash
curl http://127.0.0.1:5000/api/health
```

### 7. Make yourself an admin (optional)

Nobody can sign up as an admin. That's on purpose. You can use the demo admin above, or register normally and promote your account in MySQL:

```sql
USE valuetrack;
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

Log out and log back in. You'll land on the admin panel instead of the dashboard.

## IRDAI-registered recommendations

Every health insurance product sold in India has to be approved by **IRDAI** (the Insurance Regulatory and Development Authority of India), and gets a unique ID called a **UIN**. IRDAI publishes the full list here:

**https://irdai.gov.in/health-insurance-products**

ValueTrack can import that list and use it to back up its recommendations.

**Why it's an import and not a live scraper.** I wanted this to pull data straight from IRDAI. But IRDAI's `robots.txt` blocks all automated crawlers (`Disallow: /` for every bot), so writing a scraper for it would go against the site's own rules. ValueTrack never contacts IRDAI by itself. You open the page in your browser like any normal visitor and hand the data to ValueTrack. It's a small extra step, and it keeps the project honest.

**How to use it:**

1. Log in as an admin and open **Admin Panel → IRDAI Catalogue**.
2. In another tab, open the IRDAI link above. Filter it if you want (financial year, insurer) and show as many rows per page as it allows.
3. Get the table into ValueTrack in any one of these ways:
   - **Save the page.** Press `Ctrl+S`, choose "Webpage, HTML only", then upload the `.html` file.
   - **Copy and paste.** Select the table rows, copy them, and paste them into the text box.
   - **CSV.** Paste the table into Excel or Sheets, save it as `.csv`, then upload it.
4. Click **Import**. ValueTrack reads the insurer, UIN, product name, type, financial year, approval date and archived status. Re-importing is safe, because products are matched by UIN and updated in place.
5. IRDAI's list doesn't include premiums or cover details. So, for any product you want to recommend, click **Create plan**, then fill in the premium, ages and cover. The plan is saved with the product's UIN.
6. On the **Insurance** page, users can now set **Plan Source → IRDAI-registered plans only**. The results show the insurer, the UIN, the approval date and a green "IRDAI-registered" badge. Archived products are left out.

Rows that come in without a UIN are skipped, and the import summary tells you which ones. This happens in IRDAI's own table too, now and then.

## Running the tests

```bash
cd backend
python -m pytest -v
```

None of the tests need a database. `test_emi.py` checks the formula, the zero-interest case and that the final balance is exactly zero. `test_insurance_scoring.py` checks the age and budget filters, every scoring weight, the coverage bonus and the ranking order. `test_irdai_import.py` checks the IRDAI parser against a saved page, pasted rows and CSV, along with UIN, date and archive handling.

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
| POST   | `/insurance/request`                  | Score plans, save and return the top 5 (`source`: `all` or `irdai`) |
| GET    | `/insurance/result/<request_id>`      | Fetch a saved ranking                         |
| GET    | `/dashboard?user_id=`                 | Everything the dashboard needs in one call    |
| GET/POST/PUT/DELETE | `/admin/insurance[/<id>]`  | Manage insurance plans (admin only)           |
| GET/POST/PUT/DELETE | `/admin/categories[/<id>]` | Manage expense categories (admin only)        |
| GET/PUT | `/admin/settings`                    | Read / update system settings (admin only)    |
| GET    | `/admin/users`                        | List users (admin only)                       |
| POST   | `/admin/irdai/import`                 | Import the IRDAI list from a file or pasted text (admin only) |
| GET    | `/admin/irdai/products?q=&type=`      | Search the imported IRDAI catalogue (admin only) |

More detail, including request bodies, is in [docs/API_DOCS.md](docs/API_DOCS.md). Some older notes there still mention the CSV import I later removed.

## Known issues

I'd rather list these than have you discover them at 2 a.m. before a demo.

- **Upgrading an older database?** A fresh install from `schema.sql` has everything. If your database is older:
  - Created before **v1.0.1**? Add two columns once:

    ```sql
    USE valuetrack;
    ALTER TABLE users    ADD COLUMN monthly_budget DECIMAL(12,2) DEFAULT 0.00;
    ALTER TABLE expenses ADD COLUMN is_fixed TINYINT(1) DEFAULT 0;
    ```

  - Created before **v1.1**? Run the IRDAI migration once:

    ```bash
    mysql -u root -p < database/migrate_v1_1.sql
    ```
- **IRDAI data is only as fresh as your last import.** There's no automatic sync (see above for why). Re-import every so often to pick up new and archived products.
- **Auth is demo-grade.** Passwords are properly bcrypt-hashed, but after login the frontend keeps the user in `localStorage` and sends `user_id` with requests. The server doesn't verify the token on each call. It's fine for a college project on localhost. Don't put it on the internet like this.
- **Loans page has no "my loans" list.** You see a loan's schedule right after you create it, or by entering its ID.

## Where it's going

The wishlist is in [docs/ROADMAP.md](docs/ROADMAP.md). At the top: proper JWT auth, Alembic migrations (so schema upgrades don't need hand-written `ALTER`s), a loans list, PDF export of EMI schedules, and EMI reminder emails.

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
