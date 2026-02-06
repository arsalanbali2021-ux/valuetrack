# ValueTrack — Smart Financial & Insurance Management System

A modular, academic full-stack web application for managing loans, expenses, and insurance recommendations. Built as a 2nd-year B.Tech mini project.

## Features

- **User Authentication** — Register/login with bcrypt-hashed passwords
- **Loan & EMI Management** — Create loans, auto-generate EMI amortization schedules with Decimal precision
- **Expense Tracking** — Manual entry + CSV/XLSX bulk import using pandas
- **Insurance Recommendations** — Rule-based scoring engine, ranks top 5 plans
- **Dashboard** — Aggregated financial overview with stats

## Tech Stack

| Layer    | Technology                                         |
|----------|---------------------------------------------------|
| Frontend | HTML5, CSS3, Vanilla JavaScript (Fetch API)       |
| Backend  | Python 3.x, Flask, Flask-CORS, SQLAlchemy, bcrypt |
| Database | MySQL 8+, 3NF relational schema                  |
| Testing  | pytest                                            |

## Quick Start

```bash
# 1. Setup database
mysql -u root -p < database/schema.sql
mysql -u root -p valuetrack < database/seed_insurance.sql

# 2. Setup backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # Edit with your MySQL credentials
python app.py

# 3. Open frontend
# Open frontend/index.html in your browser, or:
cd frontend && python -m http.server 8000
# Visit http://localhost:8000
```

See [docs/SETUP.md](docs/SETUP.md) for detailed instructions.

## Project Structure

```
valuetrack/
├── backend/          # Flask API server
│   ├── app.py        # Entry point
│   ├── models.py     # SQLAlchemy ORM models
│   ├── services/     # Business logic
│   ├── routes/       # API endpoints
│   └── tests/        # Unit & integration tests
├── frontend/         # Static HTML/CSS/JS
│   ├── index.html    # Login/Register
│   ├── dashboard.html
│   ├── loans.html
│   ├── expenses.html
│   └── insurance.html
├── database/         # SQL scripts & seed data
└── docs/             # Documentation
```

## Documentation

- [SETUP.md](docs/SETUP.md) — Step-by-step local setup
- [API_DOCS.md](docs/API_DOCS.md) — Full API route specification
- [ACCEPTANCE.md](docs/ACCEPTANCE.md) — Test cases & verification steps
- [ASSUMPTIONS.md](docs/ASSUMPTIONS.md) — Design decisions & defaults
- [ROADMAP.md](docs/ROADMAP.md) — Future enhancements
