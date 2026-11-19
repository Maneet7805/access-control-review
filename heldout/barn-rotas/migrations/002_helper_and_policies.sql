-- membership check used by the policies below
create function public.is_team_member(t uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.team_members where team_id = t and user_id = auth.uid()
  );
$$;

revoke execute on function public.is_team_member(uuid) from public, anon;
grant execute on function public.is_team_member(uuid) to authenticated;

alter table public.teams enable row level security;
alter table public.team_members enable row level security;
alter table public.shift_notes enable row level security;
grant select on public.teams, public.team_members to authenticated;
grant select, insert, update, delete on public.shift_notes to authenticated;

create policy teams_for_members on public.teams
  for select to authenticated using (public.is_team_member(id));
create policy my_memberships on public.team_members
  for select to authenticated using (user_id = auth.uid());

create policy notes_team_read on public.shift_notes
  for select to authenticated using (public.is_team_member(team_id));
create policy notes_team_insert on public.shift_notes
  for insert to authenticated
  with check (author_id = auth.uid() and public.is_team_member(team_id));
create policy notes_author_update on public.shift_notes
  for update to authenticated
  using (author_id = auth.uid()) with check (author_id = auth.uid());
create policy notes_author_delete on public.shift_notes
  for delete to authenticated using (author_id = auth.uid());
