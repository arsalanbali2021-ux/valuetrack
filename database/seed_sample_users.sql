-- ============================================================
-- ValueTrack — Seed: Sample Users
-- Passwords are bcrypt-hashed.  Plaintext listed for testing.
-- Run AFTER schema.sql:  mysql -u root -p valuetrack < seed_sample_users.sql
-- ============================================================

USE valuetrack;

-- User 1:  email = alice@example.com   password = Password123
-- User 2:  email = bob@example.com     password = SecurePass1

INSERT INTO users (name, email, password_hash) VALUES
  ('Alice Johnson', 'alice@example.com',
   '$2b$12$LJ3m4ys3Lz0QFv5oX7VQ7.BGYPxUqFkHPGNqV5TZ0w9yvq8VmLZWu'),
  ('Bob Smith', 'bob@example.com',
   '$2b$12$wZgH8dG.PKjN0oYQfX9S5.3YZ8R1BvC6a5x0D7J2eQfV4mL9K3pTi');
