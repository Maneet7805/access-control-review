-- Require that an updated row in "notes" still has owner_id = auth.uid().
-- The update policy's name isn't given, so find it in pg_policies and add the
-- WITH CHECK to it. Its USING clause, roles and any existing WITH CHECK are kept.
DO $$
DECLARE
  pol record;
  new_check text;
BEGIN
  FOR pol IN
    SELECT policyname, with_check
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'notes'
      AND cmd = 'UPDATE'
  LOOP
    -- Skip if this migration has already been applied to the policy
    IF pol.with_check IS NOT NULL
       AND pol.with_check ILIKE '%owner_id%auth.uid()%' THEN
      CONTINUE;
    END IF;

    IF pol.with_check IS NULL THEN
      new_check := '(owner_id = (select auth.uid()))';
    ELSE
      new_check := format('(%s) AND (owner_id = (select auth.uid()))', pol.with_check);
    END IF;

    EXECUTE format(
      'ALTER POLICY %I ON public.notes WITH CHECK (%s)',
      pol.policyname,
      new_check
    );
  END LOOP;
END
$$;