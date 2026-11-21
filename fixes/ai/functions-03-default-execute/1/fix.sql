-- Restrict EXECUTE on public.note_count so anonymous visitors cannot call it.
-- Postgres grants EXECUTE to PUBLIC on new functions by default, so revoke that too.
REVOKE EXECUTE ON FUNCTION public."note_count" FROM PUBLIC, anon;

-- Keep the function available to the roles that legitimately need it:
-- signed-in app users and the server-side service role.
GRANT EXECUTE ON FUNCTION public."note_count" TO authenticated, service_role;

-- If anonymous visitors are meant to call this function, re-add:
-- GRANT EXECUTE ON FUNCTION public."note_count" TO anon;