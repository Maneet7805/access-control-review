-- Remove API-role access to the materialized view "all_notes".
-- Materialized views store their rows and ignore row security, so
-- security_invoker cannot protect it. The view and its data are kept.
REVOKE ALL ON public."all_notes" FROM anon, authenticated;