-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

create table public.accounts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id),
  plan_name text not null,
  paid boolean not null default false
);

insert into public.accounts (user_id, plan_name) values
  ('11111111-1111-1111-1111-111111111111', 'Plan A'),
  ('22222222-2222-2222-2222-222222222222', 'Plan B');

alter table public.accounts enable row level security;

create policy "own account" on public.accounts for select to authenticated
  using (user_id = auth.uid());
create policy "own update" on public.accounts for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Planted flaw (C1): the update policy limits which rows a user may change, not which columns,
-- so a user can mark themselves as paid.
