-- Remove API-role access to the materialized view "all_notes".
-- Materialized views store their rows and ignore row security, so the only
-- effective fix is to withdraw privileges from the roles exposed via the API.
REVOKE ALL ON public."all_notes" FROM anon, authenticated;