-- Make admin_delete_user callable only by trusted server-side roles.
-- Without an argument list, this resolves only if the function name is unique in schema public.
REVOKE EXECUTE ON FUNCTION public."admin_delete_user" FROM PUBLIC, anon, authenticated;

-- Keep the function usable from your server (service_role bypasses client-side access).
GRANT EXECUTE ON FUNCTION public."admin_delete_user" TO service_role;