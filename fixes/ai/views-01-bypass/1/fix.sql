-- Make the view "all_notes" respect row security on "notes" for the person reading it.
DO $$
BEGIN
  IF current_setting('server_version_num')::int >= 150000 THEN
    -- Postgres 15+: run the view with the rights of the caller,
    -- so row level security on "notes" applies.
    EXECUTE 'ALTER VIEW public."all_notes" SET (security_invoker = true)';
  ELSE
    -- Older versions: security_invoker is unavailable, so remove
    -- API-role access to the view instead.
    EXECUTE 'REVOKE ALL ON public."all_notes" FROM anon, authenticated';
  END IF;
END
$$;