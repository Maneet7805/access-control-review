-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

-- A shared team table: both users are in team 1 on purpose, so each sees the team's notes.
-- Notes have a team, not an owner. Membership rows are private to each user.
create table public.team_members (
  id uuid primary key default gen_random_uuid(),
  team_id uuid not null,
  user_id uuid not null references auth.users (id)
);

create table public.team_notes (
  id uuid primary key default gen_random_uuid(),
  team_id uuid not null,
  body text not null
);

insert into public.team_members (team_id, user_id) values
  ('dddddddd-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111'),
  ('dddddddd-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222');

insert into public.team_notes (team_id, body) values
  ('dddddddd-0000-0000-0000-000000000001', 'team plan'),
  ('dddddddd-0000-0000-0000-000000000001', 'team notes');

alter table public.team_members enable row level security;
alter table public.team_notes enable row level security;

create policy "own membership" on public.team_members for select to authenticated
  using (user_id = auth.uid());

create policy "team reads notes" on public.team_notes for select to authenticated
  using (team_id in (select team_id from public.team_members where user_id = auth.uid()));
