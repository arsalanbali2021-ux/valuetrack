# ValueTrack — Acceptance Test Cases

## Automated Tests

Run all tests:
```bash
cd backend
python -m pytest tests/ -v
```

### Test 1: EMI Calculation (test_emi.py)
| Scenario | Principal | Rate | Tenure | Expected |
|----------|-----------|------|--------|----------|
| Standard | ₹100,000 | 8.5% | 12 mo | EMI ≈ ₹8,718.34, final balance = 0.00 |
| Zero interest | ₹10,000 | 0% | 4 mo | EMI = ₹2,500.00, all interest = 0.00 |
| Rounding edge | ₹1,000 | 7% | 3 mo | Final balance = 0.00, total principal = ₹1,000 |

### Test 2: Expense Import (test_expense_import.py)
- Valid CSV with 3 rows → all inserted
- Mixed CSV with invalid rows → valid inserted, invalid skipped with reasons
- Invalid file extension → rejected with error

### Test 3: Insurance Scoring (test_insurance_scoring.py)
- Pre-existing condition → policy with `pre_existing_allowed=1` scores higher
- Tiny budget (₹5,000 vs ₹20,000 premium) → BudgetFit = 0, lower score
- Age out of range → AgeMatch = 0, reduced score
- Sort order → scores are descending

---

## Manual Test Steps

### 1. Register a User

```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"testpass123"}'
```

**Expected:** 201 response with `user_id`, `name`, `email`, `created_at`.

### 2. Login

```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

**Expected:** 200 response with `user_id`, `name`, `token`. Cookie `auth_token` set.

### 3. Create Loan & Verify EMI

```bash
curl -X POST http://127.0.0.1:5000/api/loans \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"principal":100000,"annual_interest_rate":8.5,"tenure_months":12,"start_date":"2025-01-01"}'
```

**Expected:** `loan_id` returned. Then:

```bash
curl http://127.0.0.1:5000/api/loans/1/schedule
```

**Expected:** 12 schedule rows. Last row: `remaining_balance = 0.00`.

### 4. Import Expenses from CSV

```bash
curl -X POST http://127.0.0.1:5000/api/expenses/import \
  -F "file=@database/expense_template.csv" \
  -F "user_id=1"
```

**Expected:**
```json
{
  "inserted": 6,
  "skipped": [
    {"row": 5, "reason": "amount must be positive"},
    {"row": 7, "reason": "invalid date"},
    {"row": 8, "reason": "amount must be positive"},
    {"row": 9, "reason": "missing category"}
  ],
  "errors": []
}
```

### 5. Insurance Request

```bash
curl -X POST http://127.0.0.1:5000/api/insurance/request \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"age":26,"pre_existing_condition":false,"annual_budget":15000}'
```

**Expected:** `request_id` + `top` array with up to 5 ranked plans, sorted by score descending.

```bash
curl http://127.0.0.1:5000/api/insurance/result/1
```

**Expected:** Same ranked results, persisted in DB.

### 6. Dashboard

```bash
curl http://127.0.0.1:5000/api/dashboard?user_id=1
```

**Expected:** JSON with `total_loans`, `total_outstanding_principal`, `monthly_expenses`, `next_emi`, `top_insurance`.

### 7. Health Check

```bash
curl http://127.0.0.1:5000/api/health
```

**Expected:** `{"status": "ok", "service": "ValueTrack API"}`

---

## Test Data

- **Demo users:** See `database/seed_sample_users.sql`
- **Insurance policies:** See `database/seed_insurance.sql` (15 policies)
- **Expense CSV:** See `database/expense_template.csv` (10 rows, 4 intentionally invalid)

---

## Security Limitations (Academic Scope)

- No MFA or multi-factor authentication
- No CSRF token protection
- No rate limiting
- Simple hash-based token (not JWT)
- No HTTPS enforcement (localhost only)
