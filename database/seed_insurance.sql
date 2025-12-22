-- ============================================================
-- ValueTrack — Seed: 15 Realistic Insurance Policies
-- Run AFTER schema.sql:  mysql -u root -p valuetrack < seed_insurance.sql
-- ============================================================

USE valuetrack;

INSERT INTO insurance
  (provider_name, plan_name, min_age, max_age, premium, coverage_amount, pre_existing_allowed, room_rent_limit)
VALUES
  ('Star Health',        'Star Comprehensive',     18, 65, 8500.00,  500000.00,  1, 5000.00),
  ('Star Health',        'Star Young Plan',        18, 35, 5000.00,  300000.00,  0, 3000.00),
  ('HDFC Ergo',          'Optima Secure',          21, 60, 12000.00, 1000000.00, 1, 7500.00),
  ('HDFC Ergo',          'Optima Restore',         25, 55, 15000.00, 1500000.00, 1, 10000.00),
  ('ICICI Lombard',      'iHealth Plan',           18, 50, 6000.00,  400000.00,  0, 4000.00),
  ('ICICI Lombard',      'Complete Health',        20, 65, 11000.00, 750000.00,  1, 6000.00),
  ('Bajaj Allianz',      'Health Guard',           18, 70, 9500.00,  500000.00,  1, 5000.00),
  ('Bajaj Allianz',      'Health Prime',           22, 55, 18000.00, 2000000.00, 1, 15000.00),
  ('Max Bupa',           'GoActive',               18, 45, 4500.00,  200000.00,  0, NULL),
  ('Max Bupa',           'Health Companion',       25, 60, 10000.00, 600000.00,  1, 5000.00),
  ('New India Assurance','Mediclaim Policy',       18, 65, 7000.00,  300000.00,  0, 3000.00),
  ('New India Assurance','Senior Mediclaim',       60, 80, 20000.00, 500000.00,  1, 7000.00),
  ('Tata AIG',           'Medicare',               18, 65, 8000.00,  400000.00,  0, 4500.00),
  ('Tata AIG',           'Medicare Premier',       20, 55, 14000.00, 1000000.00, 1, 8000.00),
  ('Niva Bupa',          'ReAssure 2.0',           18, 65, 9000.00,  500000.00,  1, 5500.00);
