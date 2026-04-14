# Changelog

All notable changes to ValueTrack, newest first.

## [1.0.0] - 2026-04-14

### Added
- Dashboard charts: spending by category, 6-month spending trend, 6-month loan balance outlook
- Recent activity list (last 5 expenses) on the dashboard
- README, FLOW.md, HOW_IT_WORKS.md and the project logo

### Changed
- Loans page and loan routes cleanup
- Updated database notes and sample users

## [0.4.0] - 2026-03-14

### Added
- Monthly budget per user with a progress bar on the expenses page
- "Fixed expense" flag for recurring costs
- Database explanation document

### Changed
- Insurance scoring rebuilt around critical illness, maternity and accident cover, with a reason shown for each result

### Removed
- CSV/XLSX expense import (and the pandas dependency)

## [0.3.0] - 2026-02-25

### Added
- User roles (`user` / `admin`)
- Admin API for insurance plans, expense categories, system settings and users
- Admin panel page

### Changed
- New dark UI theme across all pages

## [0.2.0] - 2026-02-06

### Added
- Frontend: login/register, dashboard, loans, expenses and insurance pages
- Shared `api.js` fetch wrapper
- Sample user seed and project docs (setup, API, assumptions, roadmap)

## [0.1.0] - 2026-01-04

### Added
- Flask app with auth, loans, expenses, insurance and dashboard APIs
- EMI calculation with `Decimal` precision and an exact zero final balance
- Rule-based insurance scoring (top 5 saved per request)
- CSV expense import
- MySQL schema and insurance seed data
- Unit tests for EMI and insurance scoring
