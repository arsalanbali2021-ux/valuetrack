# ValueTrack — Setup Guide

## Prerequisites

- **Python 3.9+** installed
- **MySQL 8.0+** installed and running locally
- **pip** (comes with Python)

> **Note:** This guide assumes MySQL is already installed. We do NOT install MySQL, start OS services, or use Docker.

## Step 1: Create the Database

```bash
mysql -u root -p < database/schema.sql
```

This creates the `valuetrack` database with all 7 tables.

## Step 2: Seed Insurance Data

```bash
mysql -u root -p valuetrack < database/seed_insurance.sql
```

Inserts 15 realistic insurance policies for testing.

## Step 3: (Optional) Seed Demo Users

```bash
mysql -u root -p valuetrack < database/seed_sample_users.sql
```

Creates two demo users:
- `alice@example.com` / `Password123`
- `bob@example.com` / `SecurePass1`

## Step 4: Setup Python Virtual Environment

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

## Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 6: Configure Environment

```bash
# Windows:
copy .env.example .env

# Linux/Mac:
cp .env.example .env
```

Edit `.env` with your MySQL credentials:
```
DB_USER=root
DB_PASSWORD=your_password_here
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=valuetrack
SECRET_KEY=some-random-string-here
```

## Step 7: Start the Backend

```bash
cd backend
python app.py
```

You should see:
```
==================================================
  ValueTrack API Server
  Running on http://127.0.0.1:5000
==================================================
```

## Step 8: Open the Frontend

Option A: Open `frontend/index.html` directly in your browser.

Option B: Serve with Python:
```bash
cd frontend
python -m http.server 8000
```
Then visit http://localhost:8000

## Step 9: Verify with curl

```bash
# Health check
curl http://127.0.0.1:5000/api/health

# Register a user
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Create a loan (use user_id from register response)
curl -X POST http://127.0.0.1:5000/api/loans \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"principal":100000,"annual_interest_rate":8.5,"tenure_months":12,"start_date":"2025-01-01"}'
```

## Step 10: Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

Or run individual test files:
```bash
python tests/test_emi.py
python tests/test_expense_import.py
python tests/test_insurance_scoring.py
```

## Security Notes

- Passwords are hashed with bcrypt (12 salt rounds)
- Auth uses simple token + HTTP-only cookie (academic scope)
- **Not included:** JWT, CSRF tokens, MFA, rate limiting
- **Trade-off:** Session cookie is simpler but less scalable than JWT. For this academic project, cookie-based auth is sufficient and avoids complexity of token refresh logic.
- All SQL interactions use SQLAlchemy ORM (parameterized queries) to prevent SQL injection
