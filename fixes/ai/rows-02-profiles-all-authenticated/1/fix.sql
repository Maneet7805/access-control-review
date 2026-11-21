-- Restrict reads on "profiles" to the row owner.
-- Enabling RLS is required for the policy to take effect.
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Make the migration re-runnable.
DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;

CREATE POLICY "profiles_select_own"
  ON public.profiles
  FOR SELECT
  TO authenticated
  USING (owner_id = (SELECT auth.uid()));