-- Migration: restrict read access to "phone" on public.directory.
-- Visitors (anon) and signed-in users (authenticated) lose table-wide SELECT,
-- then get SELECT back only on the columns other than "phone".
-- Existing rows, RLS policies and other privileges are left untouched.
-- Privileged server-side roles (e.g. service_role) are not affected.

DO $$
DECLARE
  public_cols text;
BEGIN
  -- Build the list of every column on directory except "phone".
  SELECT string_agg(format('%I', column_name), ', ' ORDER BY ordinal_position)
    INTO public_cols
  FROM information_schema.columns
  WHERE table_schema = 'public'
    AND table_name   = 'directory'
    AND column_name <> 'phone';

  -- Remove table-wide read access.
  REVOKE SELECT ON TABLE public.directory FROM PUBLIC;
  REVOKE SELECT ON TABLE public.directory FROM anon, authenticated;

  -- Remove any leftover column-level read access on phone.
  REVOKE SELECT (phone) ON TABLE public.directory FROM PUBLIC;
  REVOKE SELECT (phone) ON TABLE public.directory FROM anon, authenticated;

  -- Give read access back on the public columns only.
  IF public_cols IS NOT NULL THEN
    EXECUTE format(
      'GRANT SELECT (%s) ON TABLE public.directory TO anon, authenticated',
      public_cols
    );
  END IF;
END
$$;