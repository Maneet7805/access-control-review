-- Negative control: a policy that hides every row from a signed-in owner.
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

create table public.profiles (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id),
  bio text
);

insert into public.profiles (owner_id, bio) values
  ('11111111-1111-1111-1111-111111111111', 'bio of A'),
  ('22222222-2222-2222-2222-222222222222', 'bio of B');

alter table public.profiles enable row level security;

create policy "hide all" on public.profiles for select to authenticated using (false);
