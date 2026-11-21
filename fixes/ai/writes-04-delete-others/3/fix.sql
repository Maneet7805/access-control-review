-- Restrict DELETE on "notes" to the row owner and remove always-true delete policies.

ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
  p record;
  r text;
  q text;
  w text;
BEGIN
  -- Find permissive policies that allow DELETE unconditionally
  -- (DELETE or ALL policies whose USING condition is missing or always true).
  FOR p IN
    SELECT *
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'notes'
      AND permissive = 'PERMISSIVE'
      AND cmd IN ('DELETE', 'ALL')
      AND (
        qual IS NULL
        OR lower(regexp_replace(qual, '[\s()]', '', 'g')) IN ('true', '1=1')
      )
  LOOP
    r := array_to_string(
           ARRAY(SELECT CASE WHEN x = 'public' THEN 'public' ELSE quote_ident(x) END
                 FROM unnest(p.roles) AS x),
           ', ');
    q := coalesce(p.qual, 'true');
    w := coalesce(p.with_check, q);

    EXECUTE format('DROP POLICY %I ON public.notes', p.policyname);

    -- An "ALL" policy also granted SELECT/INSERT/UPDATE; keep those behaviours
    -- unchanged by recreating them as per-command policies.
    IF p.cmd = 'ALL' THEN
      EXECUTE format('CREATE POLICY %I ON public.notes FOR SELECT TO %s USING (%s)',
                     p.policyname || '_select', r, q);
      EXECUTE format('CREATE POLICY %I ON public.notes FOR INSERT TO %s WITH CHECK (%s)',
                     p.policyname || '_insert', r, w);
      EXECUTE format('CREATE POLICY %I ON public.notes FOR UPDATE TO %s USING (%s) WITH CHECK (%s)',
                     p.policyname || '_update', r, q, w);
    END IF;
  END LOOP;
END
$$;

-- Owner-only delete policy.
DROP POLICY IF EXISTS "notes_delete_own" ON public.notes;
CREATE POLICY "notes_delete_own"
  ON public.notes
  FOR DELETE
  TO authenticated
  USING (owner_id = (SELECT auth.uid()));