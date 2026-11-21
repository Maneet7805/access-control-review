-- Require notes.owner_id = auth.uid() on every INSERT policy for public.notes.
-- The existing policy names are not known, so the policies are found dynamically.
-- Any existing WITH CHECK condition and role targeting are kept, and the
-- owner check is added to them with AND.

DO $$
DECLARE
  pol record;
  new_check text;
  found boolean := false;
BEGIN
  FOR pol IN
    SELECT policyname, with_check
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'notes'
      AND cmd = 'INSERT'
  LOOP
    found := true;

    -- Skip if the owner check is already present (keeps the migration re-runnable)
    IF pol.with_check IS NOT NULL
       AND pol.with_check ILIKE '%owner_id%'
       AND pol.with_check ILIKE '%auth.uid()%' THEN
      CONTINUE;
    END IF;

    IF pol.with_check IS NULL OR btrim(pol.with_check) = '' THEN
      new_check := 'owner_id = (select auth.uid())';
    ELSE
      new_check := '(' || pol.with_check || ') AND owner_id = (select auth.uid())';
    END IF;

    EXECUTE format(
      'ALTER POLICY %I ON public.notes WITH CHECK (%s)',
      pol.policyname, new_check
    );
  END LOOP;

  -- No INSERT policy existed: create one so signed-in users can still insert their own notes
  IF NOT found THEN
    CREATE POLICY "notes_insert_own" ON public.notes
      FOR INSERT
      TO authenticated
      WITH CHECK (owner_id = (select auth.uid()));
  END IF;
END
$$;