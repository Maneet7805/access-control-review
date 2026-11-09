CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;

CREATE TABLE profiles (
  id serial PRIMARY KEY,
  owner_id text NOT NULL,
  email text NOT NULL,
  bio text
);

INSERT INTO profiles (owner_id, email, bio) VALUES
  ('user-a', 'a@example.test', 'bio of A'),
  ('user-b', 'b@example.test', 'bio of B');

GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON profiles TO anon, authenticated;
-- Planted flaw: row level security is never enabled on profiles.
