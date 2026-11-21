-- Remove the default EXECUTE that PUBLIC and anon have on this function.
REVOKE EXECUTE ON FUNCTION public."note_count" FROM PUBLIC, anon;

-- Re-grant only to the roles that need it: signed-in users and the backend service role.
GRANT EXECUTE ON FUNCTION public."note_count" TO authenticated, service_role;