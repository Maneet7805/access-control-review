-- Require owner_id = auth.uid() on inserts into public.notes.
-- Existing INSERT policies are kept and tightened (their current WITH CHECK
-- condition is preserved and the owner check is added). If none exists, one is created.

DO $$
DECLARE
  p record;
  found_policy boolean := false;
BEGIN
  FOR p IN
    SELECT policyname, with_check
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'notes'
      AND cmd = 'INSERT'
  LOOP
    found_policy := true;
    IF p.with_check IS NULL THEN
      EXECUTE format(
        'ALTER POLICY %I ON public.notes WITH CHECK (owner_id = (select auth.uid()))',
        p.policyname
      );
    ELSE
      EXECUTE format(
        'ALTER POLICY %I ON public.notes WITH CHECK ((%s) AND owner_id = (select auth.uid()))',
        p.policyname, p.with_check
      );
    END IF;
  END LOOP;

  IF NOT found_policy THEN
    EXECUTE 'CREATE POLICY "notes_insert_own" ON public.notes
             FOR INSERT TO authenticated
             WITH CHECK (owner_id = (select auth.uid()))';
  END IF;
END
$$;