-- Restrict read access to directory.phone for visitors (anon) and signed-in users (authenticated).
-- Approach: remove table-level SELECT, then grant SELECT only on the public columns
-- (every column except "phone"). Column names are discovered dynamically so that
-- no column other than "phone" needs to be named here.

BEGIN;

-- 1. Remove table-level read access (this also covers "phone").
REVOKE SELECT ON TABLE public.directory FROM anon, authenticated;

-- 2. Make sure no column-level grant on "phone" remains.
REVOKE SELECT (phone) ON TABLE public.directory FROM anon, authenticated;

-- 3. Re-grant read access on every existing column except "phone".
DO $$
DECLARE
  public_cols text;
BEGIN
  SELECT string_agg(quote_ident(column_name), ', ' ORDER BY ordinal_position)
    INTO public_cols
  FROM information_schema.columns
  WHERE table_schema = 'public'
    AND table_name   = 'directory'
    AND column_name <> 'phone';

  IF public_cols IS NOT NULL THEN
    EXECUTE format(
      'GRANT SELECT (%s) ON TABLE public.directory TO anon, authenticated',
      public_cols
    );
  END IF;
END
$$;

COMMIT;