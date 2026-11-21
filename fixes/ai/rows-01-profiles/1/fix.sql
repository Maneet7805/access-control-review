-- Lock down "profiles": each signed-in user can only access rows they own.

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Remove any existing policies on "profiles" (including permissive ones such as USING (true)),
-- so only the owner-scoped policies below remain. No tables or data are touched.
DO $$
DECLARE
  pol record;
BEGIN
  FOR pol IN
    SELECT policyname
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'profiles'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.profiles', pol.policyname);
  END LOOP;
END
$$;

-- Read: signed-in users, own rows only
CREATE POLICY profiles_select_own
  ON public.profiles
  FOR SELECT
  TO authenticated
  USING (owner_id = (SELECT auth.uid()));

-- Insert: signed-in users, new row must be owned by them
CREATE POLICY profiles_insert_own
  ON public.profiles
  FOR INSERT
  TO authenticated
  WITH CHECK (owner_id = (SELECT auth.uid()));

-- Update: only own rows, and the row must still be owned by them after the change
CREATE POLICY profiles_update_own
  ON public.profiles
  FOR UPDATE
  TO authenticated
  USING (owner_id = (SELECT auth.uid()))
  WITH CHECK (owner_id = (SELECT auth.uid()));

-- Delete: only own rows
CREATE POLICY profiles_delete_own
  ON public.profiles
  FOR DELETE
  TO authenticated
  USING (owner_id = (SELECT auth.uid()));