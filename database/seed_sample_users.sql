-- Seed: Sample Users (run after schema.sql)
-- Demo logins (local testing only):
--   alice@example.com / Password123   (user, monthly budget 25000)
--   bob@example.com   / SecurePass1   (user)
--   admin@example.com / AdminPass1    (admin)

USE valuetrack;

INSERT INTO users (name, email, password_hash, role, monthly_budget) VALUES
  ('Alice Johnson', 'alice@example.com',
   '$2b$12$RTBM5VcmvTW21Y3uOcH/6uy8f2PSxyx3Wf0YyXOWGKJ0Lwi5fvWj2', 'user', 25000.00),
  ('Bob Smith', 'bob@example.com',
   '$2b$12$1yNzc1Uy.BaOlY7VKdNDD.q9JoB0RkrJvad6w613qNjNpePHnY/ES', 'user', 0.00),
  ('Demo Admin', 'admin@example.com',
   '$2b$12$aXxKFcRp8l7ZeL/Im0/.AOTsx4lRaiNdz8Cv2rM99ftH9dl7zQeV6', 'admin', 0.00);
