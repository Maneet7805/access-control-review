-- Restrict read access to directory.phone for visitors (anon) and signed-in users (authenticated).
-- Approach: remove table-level SELECT, then grant SELECT only on every column except phone.
-- Row security policies and other privileges (INSERT/UPDATE/DELETE) are not changed.
-- Roles such as service_role and the table owner keep their access.

DO $$
DECLARE
  col_list text;
BEGIN
  -- 1. Remove table-level read access (a table-level grant would override column-level restrictions).
  REVOKE SELECT ON TABLE public.directory FROM PUBLIC;
  REVOKE SELECT ON TABLE public.directory FROM anon, authenticated;

  -- 2. Remove any leftover column-level grant on phone.
  REVOKE SELECT (phone) ON TABLE public.directory FROM PUBLIC;
  REVOKE SELECT (phone) ON TABLE public.directory FROM anon, authenticated;

  -- 3. Grant read access on all columns except phone.
  SELECT string_agg(format('%I', column_name), ', ' ORDER BY ordinal_position)
    INTO col_list
  FROM information_schema.columns
  WHERE table_schema = 'public'
    AND table_name = 'directory'
    AND column_name <> 'phone';

  IF col_list IS NOT NULL THEN
    EXECUTE format(
      'GRANT SELECT (%s) ON TABLE public.directory TO anon, authenticated',
      col_list
    );
  END IF;
END
$$;

-- Note: clients must now list columns explicitly (e.g. select=name,...) instead of
-- using SELECT * / select=*, which will be denied for anon and authenticated
-- because it includes phone.