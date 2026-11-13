-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

create table public.profiles (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id),
  email text not null,
  bio text
);

insert into public.profiles (owner_id, email, bio) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test', 'bio of A'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test', 'bio of B');

alter table public.profiles enable row level security;

-- Planted flaw (R2): every signed-in user can read every row.
create policy "any signed-in user" on public.profiles for select to authenticated
  using (true);
