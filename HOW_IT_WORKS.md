# How ValueTrack works

These are my notes on how the code fits together and why some things are the way they are. For diagrams, see [FLOW.md](FLOW.md).

## Layout

Flask does two jobs here. It serves the HTML pages from `frontend/`, and it answers everything under `/api/`. So you start one process and you're done.

The backend is split three ways, and I'd keep that split even if I rewrote the whole thing:

- `routes/` only handles HTTP. It reads the JSON, checks the fields are there and are the right type, and sends back a response.
- `services/` is where the actual work happens: EMI maths, insurance scoring, password hashing, the IRDAI import.
- `models.py` holds the SQLAlchemy classes, one per table.

When an EMI number is wrong it's in `emi_service.py`. When the status code is wrong it's in a route. That alone has saved me a lot of time.

Every response has the same shape, `{"status": ..., "message": ..., "data": ...}`. On the frontend, `api.js` unwraps it in one place. The page scripts only ever see `data`, or get an error carrying the server's message.

## Login

To register you need a name, an email and a password of at least 8 characters with a number in it. Emails are lowercased before saving, so `Arsalan@x.com` and `arsalan@x.com` count as the same account. Passwords go through bcrypt (12 rounds), and only the hash is stored.

A wrong email and a wrong password both return "Invalid email or password". If they returned different messages, the login form would tell anyone which emails are registered.

The weak spot is what happens after login. The browser keeps the user object in `localStorage` and sends `user_id` with each request. A token is set as an HttpOnly cookie, but the server never checks it. It works for a demo on localhost. It is not real auth, and JWT is the first thing on the roadmap.

## Loans and EMI

The formula is the standard one:

```
r   = annual rate / 12 / 100
EMI = P × r × (1 + r)^N / ((1 + r)^N − 1)
```

At 0% interest that divides by zero, so that case is just `P / N`.

Take ₹5,00,000 at 8.5% for 60 months. The EMI is ₹10,258.27. In month 1, ₹3,541.67 of it is interest and only ₹6,716.60 reduces the loan. Seeing that split for every month is the whole point of the loans page.

The fiddly part was rounding. With floats, sixty months of tiny errors leave a balance like `-0.03` at the end. So `emi_service.py` does two things:

1. Everything is a `Decimal`, rounded to 2 places with `ROUND_HALF_UP` at each step.
2. The last month doesn't use the standard EMI. It pays whatever principal is left plus that month's interest. That's why the final EMI can be a few paise off the others, and why the balance always ends at ₹0.00.

The loan row and all its schedule rows are saved in one transaction, so you can't end up with half a schedule. `tests/test_emi.py` checks the normal case, the 0% case and the zero final balance, without needing a database.

## Expenses and budget

An expense has a category, an amount, a date, an optional description, and a "fixed" flag for things that repeat, like rent. Set a monthly budget on the expenses page and you get a progress bar. It's green up to 75%, amber up to 100%, and red after that. The dashboard shows the same bar.

There used to be a CSV/Excel import for bank statements. It needed pandas and openpyxl, and most of the code was cleanup for each bank's slightly different CSV layout. I removed it in March. The older files in `docs/` still mention it.

## Insurance

The first version scored plans on age, budget and whether pre-existing conditions were allowed. That last one turned out to be the wrong question. When a family picks a plan, they ask "is maternity covered?" and "what about accidents?". So version two is built around critical illness, maternity and accident cover.

Age and budget are hard filters. If you're outside the plan's age range, or the monthly premium is more than your budget, the plan is dropped. Every plan left starts at 0.50 and gets:

| Need | If the plan covers it |
|------|-----------------------|
| Critical illness | +0.15 |
| Maternity | +0.15 |
| Accident | +0.10 |
| (always) | up to +0.10, based on coverage compared with the biggest plan in the table |

The maximum is 1.00. The top 5 are saved, and the best one shows up on the dashboard.

Each result also carries a list of reasons, such as "Age limit 18–65 fits", "Within budget at ₹900 a month" or "No maternity cover". A bare 0.85 doesn't tell you why a plan came first. The reasons do. The weights are plain numbers in `services/insurance_service.py`, so changing them is a one-line edit.

### The IRDAI list

The 30 sample plans in the seed file are made up. They're modelled on real products, but the numbers are mine. I wanted at least some recommendations tied to something official.

Every health product sold in India is approved by IRDAI and gets a UIN, an ID like `BAJHLIP23020V012223`. IRDAI lists them all at irdai.gov.in/health-insurance-products. I was going to scrape that page, until I saw that their `robots.txt` disallows every crawler. So it's a manual import instead. The admin opens the page in a browser, then saves it, copies the rows, or exports a CSV, and uploads that.

`services/irdai_import.py` handles all three formats. It finds the table by its "UIN" and "Product Name" headers and ignores the rest of the page. It cleans up dates and UINs, and upserts each row on the UIN. When I ran it on a real saved IRDAI page, one of the 20 rows had a blank UIN in IRDAI's own table. Rows like that get skipped and listed in the import summary.

IRDAI's list doesn't include premiums or cover details, so a product on its own can't be scored. The admin creates a plan for it, filling in premium, ages and cover, and the plan stores the UIN. With "Only IRDAI-registered plans" picked, the scorer joins plans to `irdai_products` and leaves out archived products. The scoring is the same, plus an extra reason line with the UIN, and the insurer's name under the plan.

## Dashboard

The dashboard is one request to `/api/dashboard`. It returns the loan count, the outstanding balance, the next EMI, this month's spend against budget, the last 5 expenses and your top insurance match. It also returns three charts: spend by category this year, spend per month for 6 months, and your loan balance for the next 6 months.

A month with no expenses simply doesn't appear in the SQL result, which made the trend line skip months. The route now fills those months in as ₹0.

## Admin

Admins manage plans, the IRDAI catalogue, expense categories and settings, and can see the user list. Every admin route starts with `_require_admin`, which checks that the `user_id` exists and has `role = 'admin'`, and returns a 403 otherwise. Nobody can register as an admin. You promote an account in SQL (the command is in the README).

## Database

There are 7 core tables plus `system_settings`, `expense_categories` and `irdai_products`. Foreign keys use `ON DELETE CASCADE`, so deleting a user also deletes their loans, schedule rows, expenses and insurance requests. Money is always `DECIMAL(12,2)`. `emi_schedule` has a unique key on `(loan_id, month_no)`, so a loan can't get two "month 3" rows.

For a while `schema.sql` lagged behind `models.py`. `monthly_budget` and `is_fixed` only existed in Python, and the seed file still used the old insurance columns. I only found out by building a fresh database from the repo, which is now something I do before every release. The longer database write-up (ER diagram, normalisation, viva questions) is in `PROJECT_DATABASE_Explanation.docx`.

## Where to start reading

1. `backend/app.py`, for how everything is wired up
2. `backend/services/emi_service.py`
3. `backend/tests/test_emi.py`
4. `backend/services/insurance_service.py`
5. `frontend/js/api.js`
