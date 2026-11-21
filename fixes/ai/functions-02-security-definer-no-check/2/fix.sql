-- Make set_note_body run with the caller's rights so row-level security applies.
-- Signature is not known, so every overload in public is found via the catalog.
DO $$
DECLARE
  fn regprocedure;
BEGIN
  FOR fn IN
    SELECT p.oid::regprocedure
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.proname = 'set_note_body'
  LOOP
    -- Run as the caller, not the function owner, so RLS policies are enforced.
    EXECUTE format('ALTER FUNCTION %s SECURITY INVOKER', fn);

    -- Signed-in users keep access; anonymous and public callers lose it.
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM PUBLIC', fn);
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM anon', fn);
    EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO authenticated', fn);
  END LOOP;
END
$$;

-- Note: with SECURITY INVOKER, the owner check is done by the row-level security
-- policies on the table the function updates. That table must have RLS enabled
-- with an UPDATE policy comparing auth.uid() to the row owner.