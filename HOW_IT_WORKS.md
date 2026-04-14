# How ValueTrack works

Okay, so. If you've opened this file, you either want to understand the code, you're reviewing my project, or you're future me who forgot why something is the way it is. Hi, future me.

I'll explain it the way I'd explain it to a friend sitting next to me, not the way a textbook would. If you want the arrows-and-boxes version, that's in [FLOW.md](FLOW.md).

---

## Where it started

This was my 2nd-year mini project. The original idea was small. Every loan website shows you an EMI number, but almost none of them show you the whole schedule honestly: how much of each payment is interest, how much actually reduces the loan, and what's left after each month. I wanted that.

Then it grew. If I'm tracking loans, I should track expenses too. If I'm tracking expenses, a budget makes sense. And insurance was the thing everyone at home kept arguing about ("which plan, which company, is maternity covered or not?"), so I added a matcher for that. That's how one EMI calculator turned into ValueTrack.

---

## The shape of the code

There's one Flask server. It serves the HTML pages and it answers the API calls. There's no separate frontend server and no build step. I wanted someone to be able to clone it and run it in five minutes.

The backend is split into three layers. Honestly, this split is the thing I'm proudest of structurally:

- **`routes/`** only deal with HTTP. They read the JSON, check that fields exist and are the right type, and return a response. They don't calculate anything.
- **`services/`** are where the thinking happens: EMI math, insurance scoring, password hashing.
- **`models.py`** is just SQLAlchemy classes that mirror the MySQL tables.

So when something is wrong with an EMI, I know it's in `emi_service.py`. When the API returns a weird status code, I look in the route. It saved me a lot of hunting.

Every response comes back in the same shape:

```json
{ "status": "success", "message": "Loan created successfully", "data": { ... } }
```

On the frontend, `api.js` unwraps that once, so the page scripts only ever see `data`. If something fails, it throws an error with the server's message, and the page shows it in an alert.

---

## Logging in

Registration is simple. Name, email, and a password of at least 8 characters with at least one number. The email gets lowercased so nobody can register the same address twice with different capital letters.

The password never gets stored. It goes through **bcrypt** with 12 rounds and only the hash goes into the database. When you log in, bcrypt checks your typed password against that hash.

One small detail I like: a wrong email and a wrong password give you the exact same message. If the app said "no account with this email", anyone could use the login page to check who's registered.

Now the honest part. After login, the frontend saves your user info in `localStorage` and sends your `user_id` with each request. There is a token, and it's set as an HttpOnly cookie, but the server doesn't check it on every call. For a college project running on my laptop that was fine. For anything real it isn't, and moving to JWT is the first item on the roadmap. I'd rather say this upfront than pretend.

---

## Loans and EMIs (the part I spent the most time on)

The formula itself is the standard one:

```
r   = annual rate / 12 / 100        (monthly interest rate)
EMI = P × r × (1 + r)^N / ((1 + r)^N − 1)
```

If the interest rate is 0, the formula divides by zero, so that case is just `P / N`.

Take a ₹5,00,000 loan at 8.5% for 60 months. The EMI comes to **₹10,258.27**. In month 1, ₹3,541.67 of that is interest and only ₹6,716.60 actually reduces your loan. Seeing that number is exactly why I wanted the schedule in the first place.

Here's what took me way longer than the formula. My first version used normal Python floats, and the final month's remaining balance came out as something like `-0.03` or `0.0000001`. Floats can't represent money exactly, and tiny rounding errors pile up over 60 months.

So I fixed it in two ways:

1. **Everything uses `Decimal`**, rounded to 2 places with `ROUND_HALF_UP` at every step, the way a bank would round.
2. **The last month is special.** Instead of paying the standard EMI, it pays off whatever principal is left, plus that month's interest. That's why the last EMI is sometimes a few paise different from the others, and why the balance ends at exactly ₹0.00 every time.

The loan and all of its monthly rows get saved in a single transaction. Either the whole schedule exists or none of it does.

The EMI tests in `backend/tests/test_emi.py` check all of this, including the zero-interest case and the "final balance must be exactly zero" rule. They don't need a database, so they're the quickest way to see something work.

---

## Expenses and the budget

Adding an expense is straightforward: category, amount, date, an optional description, and a "fixed" checkbox for things like rent or Netflix that come every month.

You can set a monthly budget on the expenses page. The page then shows a progress bar: green while you're fine, amber after 75%, red once you've crossed it. The same bar shows up on the dashboard.

**A bit of history:** I originally built a CSV/Excel import using pandas. You could upload your bank statement and it would bulk-insert everything. It worked, but it pulled in pandas and openpyxl, which are huge dependencies for one feature. Every bank's CSV format was different, and most of my code ended up being cleanup for messy files. I removed it and kept manual entry clean. If you see mentions of CSV import in the older docs, that's why.

---

## Insurance matching

This part went through two versions.

The first version scored plans on age match, budget fit and whether pre-existing conditions were allowed. It worked, but when I showed it to people, nobody asked about "pre-existing conditions" in the abstract. They asked "does it cover maternity?" or "what if there's an accident?". So I rebuilt it around what people actually ask.

Here's how it works now:

**Two hard filters first.** If your age isn't within the plan's age range, or the monthly premium is more than your budget, the plan is out. There's no point recommending something you can't buy or can't afford.

**Then the scoring.** Every plan that survives starts at **0.50**, and then:

| If you need…      | …and the plan covers it | Points |
|-------------------|-------------------------|--------|
| Critical illness  | yes                     | +0.15  |
| Maternity         | yes                     | +0.15  |
| Accident          | yes                     | +0.10  |
| (always)          | coverage vs. the biggest plan in the DB | up to +0.10 |

The maximum is 1.00. The top 5 get saved, so you can come back to them later, and the best one appears on your dashboard.

What I like most is that every result comes with **reasons**: "Age 18–65 limit met", "Under budget: ₹900/mo", "NO Maternity Cover". A score on its own means nothing to a person. A score with "here's why" is something you can actually decide with.

It's all rule-based. There's no machine learning and nothing is hidden. If you want to change the weights, they're right there in `services/insurance_service.py`.

---

## The dashboard

The dashboard makes one API call and gets everything back together: number of loans, total outstanding balance, the next EMI and its due date, this month's spending against your budget, your last 5 expenses, and your top insurance match.

There are three charts too: spending by category for the year, spending per month for the last 6 months, and how your loan balance will drop over the next 6 months.

A small thing that annoyed me: if you spent nothing in a month, that month simply wasn't in the query result, so the chart skipped it and the line looked broken. Now every one of the last 6 months is filled in, with ₹0 where needed.

---

## The admin panel

This came later, once I got tired of editing insurance plans directly in MySQL. Admins can add, edit and delete insurance plans, manage expense categories, change system settings, and see the list of users.

Every admin endpoint goes through the same `_require_admin` check: is there a `user_id`, does that user exist, and is their role actually `admin`? If not, you get a 403.

You can't sign up as an admin. You register normally and then someone flips your role in the database. The SQL for that is in the README.

---

## The database

Seven core tables plus two admin ones (`system_settings`, `expense_categories`). It's mostly in 3NF, with foreign keys everywhere and `ON DELETE CASCADE`, so deleting a user cleans up their loans, EMI rows, expenses and insurance requests automatically.

Money is always `DECIMAL(12,2)`, never `FLOAT`. That's the same lesson as the EMI rounding.

`emi_schedule` is a weak entity. A row only makes sense together with its loan, and `(loan_id, month_no)` is unique, so a loan can't accidentally get two "month 3" rows.

The full write-up, with the ER diagram explanation, normalization and the viva questions I prepared, is in `PROJECT_DATABASE_Explanation.docx`.

---

## Things I know aren't perfect

I'd rather be upfront:

- `schema.sql` is a little behind the Python models (`monthly_budget` on users, `is_fixed` on expenses). The README has the two `ALTER TABLE` lines to fix it. Proper migrations with Alembic would stop this from happening again.
- The insurance seed file and the insurance tests are still written for the old scoring version.
- Auth isn't production-grade (see above).
- There's no "list all my loans" view yet.

None of these are hard to fix. They're just the things that got pushed back while I was building the parts I cared about more.

---

## If you're reading the code for the first time

This is the order I'd go in:

1. `backend/app.py` to see how everything is wired together
2. `backend/services/emi_service.py`, the heart of the project
3. `backend/tests/test_emi.py`, to see that heart actually working
4. `backend/services/insurance_service.py` for the scoring
5. `frontend/js/api.js` to see how the frontend talks to all of it

That's ValueTrack. It's not huge, but every piece of it is something I had to actually figure out, and I think that shows.

— Arsalan
