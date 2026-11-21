-- Make set_note_body run with the caller's rights so row level security
-- applies to whatever it reads or writes, instead of running with the
-- function owner's privileges (which bypasses RLS).
-- No argument list is given, so this relies on set_note_body being the only
-- function with that name in the public schema.
ALTER FUNCTION public.set_note_body SECURITY INVOKER;