<p align="center">
  <img src="assets/logo.svg" alt="ValueTrack" width="72" height="72">
</p>

<h1 align="center">ValueTrack</h1>

<p align="center">Loans, monthly spending and health insurance, in one small web app.</p>

---

This was my mini project for 2nd year B.Tech. It's a college project, so please don't put your real bank details into it.

It started as an EMI calculator. Most loan sites give you one EMI figure and stop there. I wanted the whole schedule: for every month, how much goes to interest, how much actually comes off the loan, and what's left. Once that worked I added expense tracking with a monthly budget, and then an insurance matcher, because "which health plan should we take" comes up at home every year.

What it does right now:

- Creates a loan and generates its month-by-month EMI schedule. A ₹5,00,000 loan at 8.5% for 60 months comes to ₹10,258.27 a month, and the last row ends at exactly ₹0.00.
- Tracks expenses, with a monthly budget and a bar that turns amber at 75% and red once you go over.
- Takes your age, budget and what you need covered (critical illness, maternity, accident), ranks every plan, keeps the top 5, and gives a reason for each, like "Within budget at ₹900 a month" or "No maternity cover".
- Has a dashboard with outstanding balance, next EMI, this month's spend and three small charts.
- Has an admin panel for plans, expense categories and settings. It can also import IRDAI's list of approved health products (more on that below).

The longer explanation is in [HOW_IT_WORKS.md](HOW_IT_WORKS.md), and the request-by-request diagrams are in [FLOW.md](FLOW.md).

## Why it's built this way

The backend is Flask + SQLAlchemy on MySQL, and the frontend is plain HTML, CSS and JavaScript. There's no React and no build step. Flask serves the pages as well as the API, so there's only one thing to run. I wanted it to run on any machine with Python and MySQL, including a college lab PC, without setting up anything else.

All the money math uses Python's `Decimal`, not floats. The final EMI is calculated separately so the balance closes at zero instead of something like `-0.03`. The insurance score is a few fixed rules (age and budget act as hard filters, then points for each cover you need), so you can read `services/insurance_service.py` and see exactly why a plan ranked where it did. I didn't want an ML model I couldn't explain in a viva.

The look is based on an Indian bank passbook. That's on purpose, because an EMI schedule is basically a passbook page. So the app has a pale security-paper background, guilloche linework on the cover and header, ruled ledger tables with a red margin line, typewriter figures for every amount, and rubber stamps for "PAID" and "Over budget". Money is shown with Indian grouping (₹4,88,855.08), not ₹488,855.08. The fonts are Tiro Devanagari Hindi for headings, Mukta for text and Courier Prime for figures. The charts are plain HTML and CSS, with no chart library.

## Things that changed along the way

- I had a CSV/Excel import for bank statements using pandas. Every bank's CSV was different, and pandas was by far the heaviest dependency for one feature, so I took it out.
- The first insurance scorer was built around "pre-existing conditions allowed". That's not really what people ask when picking a family plan. They ask about maternity and accidents, so I rebuilt it around critical illness, maternity and accident cover.
- For a while, `schema.sql` didn't match the Python models. A fresh install would fail, and the demo logins in the seed file had fake password hashes. I only found out when I set it up from scratch on a clean database. That's fixed in v1.0.1.
- I wanted the insurance data to come from IRDAI directly, but their robots.txt blocks all crawlers. So it's an import you do by hand instead of a scraper (details below).

## Setting it up

You need Python 3.10+, MySQL 8 and Git.

```bash
git clone https://github.com/arsalanbali2021-ux/valuetrack.git
cd valuetrack
```

Create the database and load the sample data. The second file is optional and adds demo logins.

```bash
mysql -u root -p < database/schema.sql
```

```bash
mysql -u root -p valuetrack < database/seed_insurance.sql
```

```bash
mysql -u root -p valuetrack < database/seed_sample_users.sql
```

Demo logins from that file (local use only):

| Email               | Password      | Role |
|---------------------|---------------|------|
| `alice@example.com` | `Password123` | user, budget ₹25,000 |
| `bob@example.com`   | `SecurePass1` | user |
| `admin@example.com` | `AdminPass1`  | admin |

Set up Python:

```bash
cd backend
python -m venv venv
```

On Windows, `venv\Scripts\activate`. On macOS/Linux, `source venv/bin/activate`. Then:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` (`cp` on macOS/Linux, `copy` on Windows). Put your MySQL password in it, and change `SECRET_KEY` to any random string:

```
SECRET_KEY=some-long-random-string
FLASK_DEBUG=1
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=valuetrack
```

Run it (or double-click `run.bat` on Windows):

```bash
python app.py
```

Open http://127.0.0.1:5000. If the page doesn't load, `curl http://127.0.0.1:5000/api/health` should come back with `"status": "ok"`. If it doesn't, the problem is usually the MySQL password in `.env`.

You can't sign up as an admin. Use the demo admin, or promote your own account:

```sql
UPDATE valuetrack.users SET role = 'admin' WHERE email = 'you@example.com';
```

Log out and log back in, and you'll land on the admin panel.

### Upgrading an older database

A fresh install from `schema.sql` has everything. If your database is from before v1.0.1, add the two missing columns:

```sql
USE valuetrack;
ALTER TABLE users    ADD COLUMN monthly_budget DECIMAL(12,2) DEFAULT 0.00;
ALTER TABLE expenses ADD COLUMN is_fixed TINYINT(1) DEFAULT 0;
```

If it's from before v1.1, also run this once:

```bash
mysql -u root -p < database/migrate_v1_1.sql
```

## IRDAI-registered plans

Every health insurance product sold in India has to be approved by IRDAI, and each one gets a UIN, an ID like `BAJHLIP23020V012223`. IRDAI publishes the full list at https://irdai.gov.in/health-insurance-products.

My first idea was to scrape that page. Then I checked https://irdai.gov.in/robots.txt, and it says `Disallow: /` for every bot, even Googlebot. So ValueTrack never contacts IRDAI on its own. You open the page in your browser and bring the table over yourself:

1. Go to Admin → IRDAI list.
2. Open the IRDAI page in another tab. Filter it if you want, and show as many rows per page as it lets you.
3. Either save the page (Ctrl+S, "Webpage, HTML only") and upload it, or select the rows and paste them in. You can also go through Excel and upload a CSV.
4. Click Import. Products are matched on UIN, so importing the same list again only updates it.

The list only tells you a product exists. It doesn't give the premium or what it covers. So for each product you want to recommend, click "Create plan" and fill those in. On the Insurance page, users can then pick "Only IRDAI-registered plans". The results show the insurer, the UIN and the approval date, and archived products are skipped.

The data is only as recent as your last import. Re-import every few months.

## API

Everything is under `/api`, and responses look like `{"status": "success", "message": "...", "data": {...}}`.

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/health` | health check |
| POST | `/auth/register`, `/auth/login` | sign up, log in |
| PUT | `/auth/budget` | save monthly budget |
| POST | `/loans` | create a loan and its EMI schedule |
| GET | `/loans/<id>/schedule` | full schedule for one loan |
| POST / GET | `/expenses` | add an expense / list them (`?user_id=&month=&year=`) |
| POST | `/insurance/request` | rank plans and save the top 5 (`source`: `all` or `irdai`) |
| GET | `/insurance/result/<id>` | a saved ranking |
| GET | `/dashboard?user_id=` | everything the dashboard needs |
| various | `/admin/insurance`, `/admin/categories`, `/admin/settings`, `/admin/users` | admin CRUD |
| POST / GET | `/admin/irdai/import`, `/admin/irdai/products` | IRDAI import and search |

[docs/API_DOCS.md](docs/API_DOCS.md) has the request bodies. It's older than some of these changes and still mentions the CSV import.

## Tests

```bash
cd backend
python -m pytest -v
```

There are 25 tests, and none of them need a database. They cover the EMI maths (including 0% interest and the exact-zero last month), every scoring rule, and the IRDAI parser with a saved page, pasted rows and CSV.

## What's still rough

- Auth is demo-level. Passwords are hashed with bcrypt, but after login the browser keeps the user in `localStorage` and sends `user_id` with every request, and the server doesn't check the token each time. That's fine on localhost and not okay anywhere else.
- The loans page has no "all my loans" list. You see a schedule right after creating a loan, or by entering its ID.
- Schema changes are hand-written SQL files. Alembic would be the proper fix.

Next on my list: JWT auth, the loans list, PDF export of the EMI schedule, and EMI reminder emails. The longer wishlist is in [docs/ROADMAP.md](docs/ROADMAP.md).

## Other docs

- [HOW_IT_WORKS.md](HOW_IT_WORKS.md): the longer walkthrough
- [FLOW.md](FLOW.md): diagrams for each flow
- [CHANGELOG.md](CHANGELOG.md): what changed in each version
- [docs/SETUP.md](docs/SETUP.md): more setup notes
- [database/README_db.md](database/README_db.md): the tables
- `PROJECT_DATABASE_Explanation.docx`: the database write-up I prepared for my viva (ER diagram, normalisation, questions)

Made by Arsalan Bali ([@arsalanbali2021-ux](https://github.com/arsalanbali2021-ux)). If something doesn't work, open an issue.
