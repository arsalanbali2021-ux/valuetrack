# ValueTrack Database

## Overview
MySQL 8+ relational database with 7 tables in Third Normal Form (3NF).

## Setup
```bash
# 1. Create schema and tables
mysql -u root -p < schema.sql

# 2. Seed insurance policies
mysql -u root -p valuetrack < seed_insurance.sql

# 3. (Optional) Seed demo users
mysql -u root -p valuetrack < seed_sample_users.sql
```

## Tables
| Table               | Purpose                              |
|---------------------|--------------------------------------|
| `users`             | Registered user accounts             |
| `loans`             | User loan records                    |
| `emi_schedule`      | Monthly EMI breakdown (weak entity)  |
| `expenses`          | User expense records                 |
| `insurance`         | Master list of insurance policies    |
| `insurance_request` | User insurance eligibility requests  |
| `insurance_result`  | Ranked scoring results per request   |

## Files
- `schema.sql` — DDL for all tables
- `seed_insurance.sql` — 15 realistic policies
- `seed_sample_users.sql` — 2 demo users (see file for credentials)
