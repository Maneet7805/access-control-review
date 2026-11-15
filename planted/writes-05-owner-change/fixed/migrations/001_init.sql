-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

create table public.notes (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id),
  body text not null
);

insert into public.notes (owner_id, body) values
  ('11111111-1111-1111-1111-111111111111', 'note of A'),
  ('22222222-2222-2222-2222-222222222222', 'note of B');

alter table public.notes enable row level security;

create policy "own notes" on public.notes for select to authenticated
  using (owner_id = auth.uid());
create policy "own insert" on public.notes for insert to authenticated
  with check (owner_id = auth.uid());

create policy "own update" on public.notes for update to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());
