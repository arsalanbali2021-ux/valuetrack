# ValueTrack: How things flow

This is the "follow the arrows" version of the project. If [HOW_IT_WORKS.md](HOW_IT_WORKS.md) is me explaining it over chai, this is the whiteboard I'd draw while doing it.

GitHub renders the diagrams below automatically. If you're reading this somewhere else, the numbered steps under each one say the same thing.

---

## 1. The big picture

```mermaid
flowchart LR
    B[Browser<br/>HTML + CSS + JS] -- fetch /api/... --> F[Flask app<br/>app.py]
    F --> R[Routes<br/>blueprints]
    R --> S[Services<br/>business logic]
    S --> M[SQLAlchemy models]
    M --> DB[(MySQL<br/>valuetrack)]
    F -- serves static files --> B
```

There's only one server. Flask does two jobs:

1. It serves the frontend files (`index.html`, `dashboard.html`, the CSS and JS) straight from the `frontend/` folder.
2. It answers everything under `/api/...` with JSON.

Inside the backend I kept a simple rule: **routes talk HTTP, services do the thinking, models talk to the database.** A route reads the request, checks the obvious stuff (is `user_id` there, is it a number), then hands off to a service. The service does the real work and the route wraps the result in JSON.

---

## 2. What a user actually does

```mermaid
flowchart TD
    A[Open http://127.0.0.1:5000] --> B{Have an account?}
    B -- No --> C[Register<br/>name, email, password]
    C --> D[Login]
    B -- Yes --> D
    D --> E{role?}
    E -- user --> F[Dashboard]
    E -- admin --> G[Admin panel]
    F --> H[Loans]
    F --> I[Expenses]
    F --> J[Insurance]
    H --> F
    I --> F
    J --> F
    G -. can still open .-> F
```

1. You land on the login/register page.
2. After you log in, the response tells the frontend your role. Normal users go to the dashboard and admins go to the admin panel.
3. From the sidebar you move between Loans, Expenses and Insurance. Everything you do there eventually shows up on the dashboard.
4. Logging out just clears your saved user from the browser and sends you back to the login page.

---

## 3. Login, step by step

```mermaid
sequenceDiagram
    participant U as User
    participant JS as auth.js
    participant API as /api/auth/login
    participant SVC as auth_service
    participant DB as MySQL

    U->>JS: types email + password, clicks Login
    JS->>API: POST {email, password}
    API->>SVC: login_user(email, password)
    SVC->>DB: SELECT user WHERE email = ?
    DB-->>SVC: user row (with bcrypt hash)
    SVC->>SVC: bcrypt.checkpw(password, hash)
    SVC-->>API: user_id, name, role, budget, token
    API-->>JS: JSON + HttpOnly cookie
    JS->>JS: save user in localStorage
    JS->>U: redirect to dashboard.html or admin.html
```

- The email is trimmed and lowercased before lookup, so `Arsalan@X.com` and `arsalan@x.com` are the same person.
- A wrong email and a wrong password give the same error ("Invalid email or password"). That's on purpose. I don't want to tell anyone which emails are registered.
- Registration follows the same path. It checks that the name and email exist, that the password is 8+ characters with at least one number, and that the email isn't already taken. Then it bcrypt-hashes the password (12 rounds) and saves the user.

---

## 4. Creating a loan

```mermaid
sequenceDiagram
    participant U as User
    participant JS as loans.js
    participant API as POST /api/loans
    participant EMI as emi_service
    participant DB as MySQL

    U->>JS: principal, rate, tenure, start date
    JS->>API: POST {user_id, principal, annual_interest_rate, tenure_months, start_date}
    API->>API: check fields present + numeric
    API->>EMI: create_loan_with_schedule(...)
    EMI->>DB: INSERT loan (flush to get loan_id)
    EMI->>EMI: calculate_emi() + generate_schedule()
    loop every month 1..N
        EMI->>DB: INSERT emi_schedule row
    end
    EMI->>DB: COMMIT
    EMI-->>API: loan_id, emi, created_at
    API-->>JS: 201 Created
    JS->>API: GET /api/loans/{id}/schedule
    API-->>JS: loan + every month's breakdown
    JS->>U: renders the schedule table
```

The loan and all its EMI rows are saved in **one transaction**. If anything fails halfway, you don't end up with a loan that has 23 of its 60 months.

---

## 5. Logging an expense and the budget

```mermaid
flowchart TD
    A[Expenses page] --> B[Fill category, amount, date,<br/>description, fixed?]
    B --> C[POST /api/expenses]
    C --> D{valid?<br/>category set, amount > 0,<br/>date is YYYY-MM-DD}
    D -- no --> E[400 + message shown on page]
    D -- yes --> F[INSERT into expenses]
    F --> G[Page reloads list for the month<br/>GET /api/expenses?month=&year=]
    G --> H[Total vs monthly budget<br/>progress bar]
    A --> I[Edit budget]
    I --> J[PUT /api/auth/budget]
    J --> K[users.monthly_budget updated<br/>+ localStorage copy updated]
    K --> H
```

The progress bar is green until you've used 75% of your budget, amber between 75% and 100%, and red once you're over. The dashboard uses the same colours.

---

## 6. Getting insurance recommendations

```mermaid
flowchart TD
    A[Insurance page:<br/>age, monthly budget,<br/>need critical illness? maternity? accident?] --> B[POST /api/insurance/request]
    B --> C[Save the request row]
    C --> D[Load every plan from insurance table]
    D --> E{For each plan}
    E --> F{Age within<br/>min_age..max_age?}
    F -- no --> X[score 0, dropped]
    F -- yes --> G{monthly premium<br/>≤ budget?}
    G -- no --> X
    G -- yes --> H[start at 0.50]
    H --> I[+0.15 if critical illness needed and covered]
    I --> J[+0.15 if maternity needed and covered]
    J --> K[+0.10 if accident needed and covered]
    K --> L[+0.10 × coverage / biggest coverage]
    L --> M[Sort by score, keep top 5]
    X --> M
    M --> N[Save top 5 in insurance_result]
    N --> O[Return plans + reasons<br/>e.g. 'Under budget: ₹900/mo']
```

The best possible score is 1.00. A plan that only passes the age and budget filters starts at 0.50 and can only climb from there. The reasons list is what you see as the little ticks and crosses on each card.

### 6b. With "IRDAI-registered plans only"

```mermaid
flowchart TD
    A[Admin opens irdai.gov.in/health-insurance-products<br/>in a normal browser] --> B[Saves the page / copies rows / exports CSV]
    B --> C[Admin panel: IRDAI Catalogue → Import]
    C --> D[POST /api/admin/irdai/import]
    D --> E[Find the table by its UIN + Product Name headers]
    E --> F{Row has UIN,<br/>insurer, product?}
    F -- no --> G[skipped, listed in the summary]
    F -- yes --> H[Upsert into irdai_products<br/>matched on UIN]
    H --> I[Admin clicks Create plan<br/>adds premium, ages, cover]
    I --> J[insurance row saved with irdai_uin]
    J --> K[User picks Plan Source:<br/>IRDAI-registered plans only]
    K --> L[POST /api/insurance/request<br/>source = irdai]
    L --> M[Only plans joined to a<br/>non-archived IRDAI product]
    M --> N[Same scoring as above]
    N --> O[Results show insurer, UIN,<br/>approval date + green badge]
```

ValueTrack never fetches anything from IRDAI. Their `robots.txt` blocks all bots, so the admin brings the file in by hand.

---

## 7. The dashboard call

One request, `GET /api/dashboard?user_id=…`, collects everything:

```mermaid
flowchart LR
    D[GET /api/dashboard] --> A[Total loans count]
    D --> B[Outstanding balance<br/>next unpaid EMI row per loan]
    D --> C[This month's spend vs budget]
    D --> E[5 most recent expenses]
    D --> F[Next EMI due]
    D --> G[Top plan from latest insurance request]
    D --> H[Charts]
    H --> H1[Spend by category, this year]
    H --> H2[Spend per month, last 6 months]
    H --> H3[Loan balance, next 6 months]
```

Months with no spending still show up as ₹0 in the trend chart. Without that the line just skipped months, which looked broken.

---

## 8. Admin flow

```mermaid
flowchart TD
    A[Admin logs in] --> B[admin.html]
    B --> C{Every /api/admin call}
    C --> D[_require_admin:<br/>user_id present? user exists?<br/>role == 'admin'?]
    D -- no --> E[400 / 404 / 403]
    D -- yes --> F[Insurance plans CRUD]
    D -- yes --> G[Expense categories CRUD]
    D -- yes --> H[System settings]
    D -- yes --> I[View users]
```

Every admin endpoint runs the same check first. The check looks up the user from the `user_id` sent with the request and rejects anyone who isn't an admin.

---

## 9. How the tables connect

```mermaid
erDiagram
    users ||--o{ loans : has
    loans ||--|{ emi_schedule : "broken into"
    users ||--o{ expenses : logs
    users ||--o{ insurance_request : submits
    insurance_request ||--o{ insurance_result : produces
    insurance ||--o{ insurance_result : "ranked in"
    irdai_products |o--o{ insurance : "UIN of"
    system_settings
    expense_categories
```

Delete a user and their loans, EMI rows, expenses and insurance requests all go with them (`ON DELETE CASCADE`). No orphan rows lying around.
