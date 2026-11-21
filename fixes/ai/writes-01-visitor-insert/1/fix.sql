-- Ensure row level security is enabled on notes (no-op if already enabled)
ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;

-- Replace the policy if this migration is re-run
DROP POLICY IF EXISTS "notes_insert_own" ON public.notes;

-- Only signed-in users may insert, and only rows they own
CREATE POLICY "notes_insert_own"
  ON public.notes
  FOR INSERT
  TO authenticated
  WITH CHECK (
    auth.uid() IS NOT NULL
    AND owner_id = auth.uid()
  );