-- Restrict UPDATE on public.notes to the row owner, and keep the owner from changing.

ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
  p record;
  role_list text;
  q text;
  wc text;
BEGIN
  -- Remove every permissive policy that allows UPDATE (including any with an
  -- always-true condition). Permissive policies are OR-ed together, so a single
  -- loose one would defeat the new owner-only policy.
  -- Policies that cover ALL commands are split into separate SELECT, INSERT and
  -- DELETE policies with the same conditions first, so those operations keep
  -- working exactly as before.
  FOR p IN
    SELECT policyname, cmd, roles, qual, with_check
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'notes'
      AND permissive = 'PERMISSIVE'
      AND cmd IN ('UPDATE', 'ALL')
  LOOP
    IF p.cmd = 'ALL' THEN
      SELECT string_agg(CASE WHEN r = 'public' THEN 'public' ELSE quote_ident(r) END, ', ')
        INTO role_list
        FROM unnest(p.roles) AS r;
      q  := coalesce(p.qual, 'true');
      wc := coalesce(p.with_check, q);

      EXECUTE format('DROP POLICY IF EXISTS %I ON public.notes', left(p.policyname, 50) || '_select');
      EXECUTE format('CREATE POLICY %I ON public.notes FOR SELECT TO %s USING (%s)',
                     left(p.policyname, 50) || '_select', role_list, q);

      EXECUTE format('DROP POLICY IF EXISTS %I ON public.notes', left(p.policyname, 50) || '_insert');
      EXECUTE format('CREATE POLICY %I ON public.notes FOR INSERT TO %s WITH CHECK (%s)',
                     left(p.policyname, 50) || '_insert', role_list, wc);

      EXECUTE format('DROP POLICY IF EXISTS %I ON public.notes', left(p.policyname, 50) || '_delete');
      EXECUTE format('CREATE POLICY %I ON public.notes FOR DELETE TO %s USING (%s)',
                     left(p.policyname, 50) || '_delete', role_list, q);
    END IF;

    EXECUTE format('DROP POLICY %I ON public.notes', p.policyname);
  END LOOP;
END
$$;

-- Owner-only UPDATE: USING limits which rows can be changed,
-- WITH CHECK ensures the changed row still belongs to the user.
DROP POLICY IF EXISTS notes_update_own ON public.notes;
CREATE POLICY notes_update_own
  ON public.notes
  FOR UPDATE
  TO authenticated
  USING (owner_id = (SELECT auth.uid()))
  WITH CHECK (owner_id = (SELECT auth.uid()));