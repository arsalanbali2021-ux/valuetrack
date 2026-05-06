# ValueTrack Database

## Overview
MySQL 8+ relational database: 7 core tables plus 3 admin tables, mostly in Third Normal Form (3NF).

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
| `system_settings`   | Key-value settings (admin)           |
| `expense_categories`| Expense categories (admin)           |
| `irdai_products`    | IRDAI register of approved products (imported by admin) |

## Files
- `schema.sql` — DDL for all tables
- `seed_insurance.sql` — 30 sample plans (illustrative premiums, not real quotes)
- `seed_sample_users.sql` — 2 demo users + 1 demo admin (credentials in the file header)
- `migrate_v1_1.sql` — one-time upgrade for databases created before v1.1 (adds `insurance.irdai_uin` and `irdai_products`)
