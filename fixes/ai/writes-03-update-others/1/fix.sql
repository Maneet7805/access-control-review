-- Migration: restrict updates on "notes" to the row owner

BEGIN;

-- Make sure row level security is on and applies to the table owner role too.
ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;

-- Remove existing UPDATE-only policies. Policies are permissive and OR together,
-- so one with an always-true condition would let any user change any note.
-- Only policies are dropped; no tables or data are touched.
DO $$
DECLARE
  p record;
BEGIN
  FOR p IN
    SELECT policyname
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename  = 'notes'
      AND cmd        = 'UPDATE'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.notes', p.policyname);
  END LOOP;
END
$$;

-- Owner-only update: the existing row must belong to the user (USING)
-- and the changed row must still belong to the user (WITH CHECK).
DROP POLICY IF EXISTS notes_update_own ON public.notes;
CREATE POLICY notes_update_own
  ON public.notes
  AS PERMISSIVE
  FOR UPDATE
  TO authenticated
  USING (owner_id = (SELECT auth.uid()))
  WITH CHECK (owner_id = (SELECT auth.uid()));

-- Guard: a restrictive policy is ANDed with every permissive policy, including
-- any FOR ALL policy that also covers UPDATE and might have an always-true
-- condition. This ensures updates can never bypass the owner check.
-- SELECT, INSERT and DELETE behaviour is unchanged.
DROP POLICY IF EXISTS notes_update_owner_guard ON public.notes;
CREATE POLICY notes_update_owner_guard
  ON public.notes
  AS RESTRICTIVE
  FOR UPDATE
  USING (owner_id = (SELECT auth.uid()))
  WITH CHECK (owner_id = (SELECT auth.uid()));

COMMIT;