# Changelog

All notable changes to ValueTrack, newest first.

## [1.1.0] - 2026-05-06

### Added
- IRDAI product catalogue: admins import IRDAI's public list of approved health insurance products (saved page, pasted rows or CSV)
- Plans can be linked to an IRDAI UIN, and "Create plan" works straight from a catalogue entry
- "IRDAI-registered plans only" option on the insurance page; results show insurer, UIN and approval date
- `migrate_v1_1.sql` for upgrading existing databases
- 13 parser tests for the IRDAI import

### Notes
- ValueTrack doesn't scrape IRDAI, because its robots.txt disallows all crawlers. The admin downloads or copies the list in a browser and imports it.

## [1.0.1] - 2026-04-23

### Fixed
- `schema.sql` now creates `users.monthly_budget` and `expenses.is_fixed`
- SQL comments that MySQL refused to parse (`--` needs a space after it)
- Insurance seed rewritten for the current insurance table (30 plans)
- Sample users now have real bcrypt hashes, plus a demo admin account
- Insurance scoring tests rewritten for the current scorer (12 tests passing)

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
