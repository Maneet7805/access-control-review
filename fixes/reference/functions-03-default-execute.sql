create or replace function public.note_count() returns bigint
  language sql security invoker set search_path = public as $$
  select count(*) from public.notes;
$$;

revoke execute on function public.note_count() from public, anon;
grant execute on function public.note_count() to authenticated;
