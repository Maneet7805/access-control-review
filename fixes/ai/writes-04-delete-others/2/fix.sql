-- Restrict DELETE on public.notes to the row's owner.

ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
  p record;
  roles_sql text;
BEGIN
  FOR p IN
    SELECT policyname, cmd, roles, qual, with_check
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename  = 'notes'
      AND permissive = 'PERMISSIVE'
      AND cmd IN ('DELETE', 'ALL')
      AND policyname <> 'notes_delete_own'
  LOOP
    SELECT string_agg(CASE WHEN r = 'public' THEN 'public' ELSE quote_ident(r) END, ', ')
      INTO roles_sql
      FROM unnest(p.roles) AS r;

    -- Remove the existing policy. Any permissive DELETE policy (for example one
    -- with USING (true)) would otherwise override the owner-only rule.
    EXECUTE format('DROP POLICY %I ON public.notes', p.policyname);

    -- A FOR ALL policy also granted select/insert/update, so re-create those
    -- permissions without the delete part to keep the app working.
    IF p.cmd = 'ALL' THEN
      IF p.qual IS NOT NULL THEN
        EXECUTE format('CREATE POLICY %I ON public.notes FOR SELECT TO %s USING (%s)',
                       p.policyname || '_select', roles_sql, p.qual);
      END IF;

      IF coalesce(p.with_check, p.qual) IS NOT NULL THEN
        EXECUTE format('CREATE POLICY %I ON public.notes FOR INSERT TO %s WITH CHECK (%s)',
                       p.policyname || '_insert', roles_sql, coalesce(p.with_check, p.qual));
      END IF;

      IF p.qual IS NOT NULL THEN
        EXECUTE format('CREATE POLICY %I ON public.notes FOR UPDATE TO %s USING (%s)%s',
                       p.policyname || '_update', roles_sql, p.qual,
                       CASE WHEN p.with_check IS NOT NULL
                            THEN ' WITH CHECK (' || p.with_check || ')'
                            ELSE '' END);
      END IF;
    END IF;
  END LOOP;
END $$;

DROP POLICY IF EXISTS "notes_delete_own" ON public.notes;

CREATE POLICY "notes_delete_own"
  ON public.notes
  FOR DELETE
  TO authenticated
  USING (owner_id = (SELECT auth.uid()));