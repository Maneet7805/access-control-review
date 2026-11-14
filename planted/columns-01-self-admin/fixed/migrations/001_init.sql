-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

create table public.members (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id),
  display_name text not null,
  role text not null default 'member'
);

insert into public.members (user_id, display_name) values
  ('11111111-1111-1111-1111-111111111111', 'Member A'),
  ('22222222-2222-2222-2222-222222222222', 'Member B');

alter table public.members enable row level security;

create policy "own member" on public.members for select to authenticated
  using (user_id = auth.uid());
create policy "own update" on public.members for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Fix: users may change only their display name. role is not updatable by them.
revoke update on public.members from authenticated;
grant update (display_name) on public.members to authenticated;
