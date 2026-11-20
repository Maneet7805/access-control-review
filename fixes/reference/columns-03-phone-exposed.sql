revoke select on public.directory from anon, authenticated;
grant select (id, display_name) on public.directory to anon, authenticated;
