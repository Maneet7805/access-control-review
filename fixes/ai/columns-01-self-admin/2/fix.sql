-- Migration: prevent signed-in users from updating members.role

DO $$
DECLARE
  col_list text;
BEGIN
  -- Table-level UPDATE would override any column-level revoke, so remove it first.
  REVOKE UPDATE ON TABLE public.members FROM PUBLIC;
  REVOKE UPDATE ON TABLE public.members FROM anon;
  REVOKE UPDATE ON TABLE public.members FROM authenticated;

  -- Also clear any existing column-level UPDATE grant on "role".
  REVOKE UPDATE (role) ON TABLE public.members FROM PUBLIC;
  REVOKE UPDATE (role) ON TABLE public.members FROM anon;
  REVOKE UPDATE (role) ON TABLE public.members FROM authenticated;

  -- Re-grant UPDATE on every column except "role", so existing user-facing
  -- updates (profile edits, etc.) keep working without naming other columns.
  SELECT string_agg(format('%I', column_name), ', ' ORDER BY ordinal_position)
    INTO col_list
  FROM information_schema.columns
  WHERE table_schema = 'public'
    AND table_name = 'members'
    AND column_name <> 'role';

  IF col_list IS NOT NULL THEN
    EXECUTE format(
      'GRANT UPDATE (%s) ON TABLE public.members TO authenticated',
      col_list
    );
  END IF;
END
$$;

-- Note: columns added to public.members later will not be user-updatable
-- until UPDATE is granted on them explicitly. Role changes must be made by
-- a privileged role (service_role / postgres / a SECURITY DEFINER function).