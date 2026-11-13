-- Supabase baseline for the sandbox. Applied as supabase_admin on the Supabase database image, before any app migration.
--
-- Already in the image, so not repeated here (checked by scripts/probe_images.py, see docs/decisions/sandbox-image.md):
--   roles anon, authenticated, service_role (service_role bypasses row security), schema auth with auth.users,
--   and default privileges that give anon, authenticated and service_role full access to new tables in public.
--   The Supabase row level security page confirms that service_role has bypassrls and that these default grants exist.
--
-- Missing or different in the image, so set here:
--   auth.jwt() does not exist, and auth.uid() / auth.role() read only the old per-claim settings.
--   The Supabase pages do not say which setting these functions read. We accept both the old per-claim
--   settings and the whole-token setting request.jwt.claims, which is how hosted Supabase behaves as far as
--   we know. [Likely] Verify against a hosted project when one is available.

create or replace function auth.uid() returns uuid language sql stable as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;

create or replace function auth.role() returns text language sql stable as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim.role', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role')
  )::text
$$;

create or replace function auth.jwt() returns jsonb language sql stable as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim', true), ''),
    nullif(current_setting('request.jwt.claims', true), '')
  )::jsonb
$$;

alter function auth.jwt() owner to supabase_auth_admin;
