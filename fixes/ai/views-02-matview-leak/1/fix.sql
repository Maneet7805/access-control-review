-- Remove API access to the materialized view "all_notes".
-- Materialized views store their rows and ignore row security,
-- so the only effective fix is to remove privileges from the API roles.

REVOKE ALL ON public."all_notes" FROM anon, authenticated;

-- Also stop PUBLIC (which anon/authenticated inherit from) from reading it.
REVOKE ALL ON public."all_notes" FROM PUBLIC;