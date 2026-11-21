-- Require owner_id = auth.uid() on every insert into public.notes.
-- Existing INSERT policies are amended in place, so their names, roles and
-- existing conditions are kept and the new check is ANDed on.
-- Policies with cmd ALL also permit inserts, so they get the same check.

ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
  p record;
BEGIN
  FOR p IN
    SELECT policyname, cmd, qual, with_check
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename  = 'notes'
      AND cmd IN ('INSERT', 'ALL')
  LOOP
    EXECUTE format(
      'ALTER POLICY %I ON public.notes WITH CHECK ((%s) AND owner_id = (SELECT auth.uid()))',
      p.policyname,
      COALESCE(p.with_check, p.qual, 'true')
    );
  END LOOP;
END
$$;