# ValueTrack — Roadmap (v2 Ideas)

## Security Enhancements
- [ ] Replace simple token with **JWT** (access + refresh tokens)
- [ ] Add **CSRF token** protection for state-changing requests
- [ ] Implement **rate limiting** on auth endpoints
- [ ] Add **HTTPS** enforcement (Let's Encrypt + reverse proxy)
- [ ] Input sanitization middleware

## Infrastructure
- [ ] **Docker Compose** setup (Flask + MySQL + Nginx)
- [ ] **CI/CD pipeline** (GitHub Actions: lint, test, build)
- [ ] Environment-specific configs (dev, staging, prod)
- [ ] Database migrations with **Alembic**

## Features
- [ ] **Expense categories analytics** — pie chart, bar chart with Chart.js
- [ ] **Loan comparison** — compare multiple loan offers side-by-side
- [ ] **Insurance policy details** — full policy terms, claim process info
- [ ] **PDF export** — generate EMI schedule and expense reports as PDF
- [ ] **Email notifications** — upcoming EMI reminders
- [ ] **Multi-currency support** — store currency code with amounts
- [ ] **Recurring expenses** — auto-create monthly expenses

## Performance
- [ ] **Chunked file reads** for large CSV/XLSX imports
- [ ] **Database connection pooling** optimization
- [ ] **Pagination** for expense list API
- [ ] **Redis caching** for dashboard aggregation queries

## Mobile
- [ ] **Progressive Web App** (PWA) — service worker, offline support
- [ ] **React Native** or **Flutter** mobile app consuming the same API

## Testing
- [ ] End-to-end tests with **Selenium** or **Playwright**
- [ ] Load testing with **Locust** or **k6**
- [ ] Code coverage reporting
