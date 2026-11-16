-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

-- A public profile page. Names are meant to be public; phone numbers are not.
create table public.directory (
  id uuid primary key default gen_random_uuid(),
  display_name text not null,
  phone text
);

insert into public.directory (display_name, phone) values
  ('Member A', '+60 12-000 0001'),
  ('Member B', '+60 12-000 0002');

alter table public.directory enable row level security;

create policy "public profiles" on public.directory for select to anon, authenticated
  using (true);

-- Planted flaw (C2): the policy limits rows, not columns, so anyone who may read the
-- profile page can also read every phone number.
