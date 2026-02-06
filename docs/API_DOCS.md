# ValueTrack — API Documentation

Base URL: `http://127.0.0.1:5000/api`

All endpoints return JSON. Authentication is via cookie (set on login).

---

## Health Check

### `GET /api/health`
```json
// Response 200
{ "status": "ok", "service": "ValueTrack API" }
```

---

## Authentication

### `POST /api/auth/register`

Register a new user account.

**Request:**
```json
{ "name": "Alice Johnson", "email": "alice@example.com", "password": "Password123" }
```

**Response 201:**
```json
{
  "user_id": 1,
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "created_at": "2025-01-01 00:00:00"
}
```

**Response 400:**
```json
{ "error": "Email already registered" }
```

### `POST /api/auth/login`

**Request:**
```json
{ "email": "alice@example.com", "password": "Password123" }
```

**Response 200:**
```json
{ "user_id": 1, "name": "Alice Johnson", "token": "sha256-hex-string" }
```
Also sets `auth_token` HTTP-only cookie.

**Response 401:**
```json
{ "error": "Invalid email or password" }
```

---

## Loans

### `POST /api/loans`

Create a loan and auto-generate EMI schedule.

**Request:**
```json
{
  "user_id": 1,
  "principal": 100000,
  "annual_interest_rate": 8.5,
  "tenure_months": 12,
  "start_date": "2025-01-01"
}
```

**Response 201:**
```json
{ "loan_id": 1, "emi": 8718.34, "created_at": "2025-01-01 00:00:00" }
```

### `GET /api/loans/{loan_id}/schedule`

**Response 200:**
```json
{
  "loan_id": 1,
  "loan": { "loan_id": 1, "principal": 100000.0, "..." : "..." },
  "schedule": [
    {
      "emi_id": 1, "loan_id": 1, "month_no": 1,
      "emi_amount": 8718.34, "principal_component": 8010.01,
      "interest_component": 708.33, "remaining_balance": 91989.99,
      "due_date": "2025-02-01"
    }
  ]
}
```

---

## Expenses

### `POST /api/expenses`

Create a single expense.

**Request:**
```json
{
  "user_id": 1,
  "category": "Food",
  "amount": 250.00,
  "expense_date": "2025-10-01",
  "description": "Grocery shopping"
}
```

**Response 201:** Returns the created expense object.

### `POST /api/expenses/import`

Import expenses from CSV/XLSX file.

**Request:** `multipart/form-data`
- `file`: The CSV or XLSX file
- `user_id`: User ID (form field)

**Response 200:**
```json
{
  "inserted": 7,
  "skipped": [
    { "row": 5, "reason": "amount must be positive" },
    { "row": 7, "reason": "invalid date" }
  ],
  "errors": []
}
```

**Response 400:** Missing columns or invalid file type.
**Response 413:** File exceeds 10MB limit.

### `GET /api/expenses?user_id=1&month=10&year=2025`

**Response 200:**
```json
{
  "expenses": [ { "expense_id": 1, "category": "Food", "amount": 250.0, "..." : "..." } ],
  "total": 1250.50,
  "count": 5
}
```

---

## Insurance

### `POST /api/insurance/request`

Score and rank insurance plans for user profile.

**Request:**
```json
{
  "user_id": 1,
  "age": 26,
  "pre_existing_condition": false,
  "annual_budget": 15000.00
}
```

**Response 200:**
```json
{
  "request_id": 1,
  "top": [
    {
      "insurance_id": 5, "score": 0.78, "rank": 1,
      "provider": "ICICI Lombard", "plan_name": "iHealth Plan",
      "premium": 6000.0, "coverage": 400000.0
    }
  ]
}
```

### `GET /api/insurance/result/{request_id}`

**Response 200:** Same format as above with persisted results.

---

## Dashboard

### `GET /api/dashboard?user_id=1`

**Response 200:**
```json
{
  "total_loans": 3,
  "total_outstanding_principal": 34500.00,
  "monthly_expenses": 7200.00,
  "next_emi": { "loan_id": 5, "due_date": "2025-03-05", "amount": 2500.00 },
  "top_insurance": { "insurance_id": 9, "provider": "Max Bupa", "rank_score": 0.78 }
}
```
