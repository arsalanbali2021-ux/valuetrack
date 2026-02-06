# ValueTrack — Assumptions & Design Decisions

## Defaults Chosen

1. **Auth token format:** Simple SHA-256 hash of `user_id + timestamp + random`. Stored in localStorage on frontend and as HTTP-only cookie. This is NOT production-safe but sufficient for academic demonstration.

2. **Bcrypt rounds:** 12 (configurable via `Config.BCRYPT_ROUNDS`). Higher rounds increase security but slow down registration/login.

3. **EMI rounding:** Python `Decimal` with `ROUND_HALF_UP` at every step. Last month's principal is set to remaining balance to guarantee zero final balance.

4. **Insurance scoring weights:** AgeMatch=0.30, BudgetFit=0.40, PreExistingSupport=0.20, CoverageBonus=0.10. These are hardcoded per spec. To tune, edit `insurance_service.py`.

5. **File upload limit:** 10MB. Configurable via `Config.MAX_CONTENT_LENGTH`.

6. **Expense date format:** Accepts multiple formats via `pandas.to_datetime()`, stores as `YYYY-MM-DD`.

7. **Currency:** Indian Rupees (₹) assumed in UI. Backend stores plain `DECIMAL(12,2)` without currency code.

## Architectural Decisions

8. **No JWT:** Per spec, using session cookie. JWT would require token refresh logic, blacklisting, etc.

9. **No Docker:** Local development only. MySQL must be pre-installed.

10. **SQLAlchemy ORM only:** No raw SQL to prevent injection. Parameterized queries where raw SQL is unavoidable.

11. **No frontend build step:** All HTML/CSS/JS served statically. No webpack, no transpilation.

12. **Single transaction for imports:** All valid expense rows are inserted in one transaction. If the DB fails mid-insert, all rows in that batch are rolled back.

## Known Limitations

13. **Concurrent imports:** Two simultaneous CSV imports for the same user could insert duplicate rows. Mitigation: document transactional behavior. For scaling, add row-level locks or a unique constraint on (user_id, category, amount, expense_date).

14. **Large file memory:** pandas loads the entire file into memory. For very large files (>10MB), this could cause issues. The 10MB limit mitigates this.

15. **Pre-existing allowed flag:** Stored as `TINYINT(1)` in MySQL, treated as boolean in Python. Values: 0=false, 1=true.

16. **No ML:** Insurance scorer is deterministic rule-based. Weights are fixed. Document tuning approach in ROADMAP.

17. **CORS origins:** Configured for `localhost:8000`, `localhost:5500`, and `null` (for `file://` protocol). Add more origins in `app.py` if needed.
