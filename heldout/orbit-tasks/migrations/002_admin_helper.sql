create function public.is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.staff where user_id = auth.uid());
$$;

revoke execute on function public.is_admin() from public, anon;
grant execute on function public.is_admin() to authenticated;

alter table public.staff enable row level security;
alter table public.tasks enable row level security;

create policy staff_self on public.staff
  for select to authenticated using (user_id = auth.uid());

create policy tasks_owner_or_admin on public.tasks
  for all to authenticated
  using (user_id = auth.uid() or public.is_admin())
  with check (user_id = auth.uid() or public.is_admin());

grant select on public.staff to authenticated;
grant select, insert, update, delete on public.tasks to authenticated;
grant all on public.staff, public.tasks to service_role;
