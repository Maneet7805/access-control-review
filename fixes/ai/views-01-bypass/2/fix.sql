-- Make public.all_notes respect the caller's rights (and thus row security on public.notes).
DO $$
BEGIN
  IF to_regclass('public.all_notes') IS NULL THEN
    RAISE NOTICE 'public.all_notes not found; nothing to do';
    RETURN;
  END IF;

  IF current_setting('server_version_num')::int >= 150000 THEN
    -- Postgres 15+: run the view with the privileges of the person querying it,
    -- so RLS policies on public.notes apply.
    EXECUTE 'ALTER VIEW public."all_notes" SET (security_invoker = true)';
  ELSE
    -- Older Postgres: security_invoker is unavailable, so remove API access to the view.
    EXECUTE 'REVOKE ALL ON public."all_notes" FROM anon, authenticated';
  END IF;
END
$$;