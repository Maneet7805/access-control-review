-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

-- A public profile page: names and bios are meant to be read by everyone, signed in or not.
-- No owner column and no private column. Nobody can write.
create table public.profiles_public (
  id uuid primary key default gen_random_uuid(),
  username text not null,
  bio text
);

insert into public.profiles_public (username, bio) values
  ('member-a', 'bio of A'),
  ('member-b', 'bio of B');

alter table public.profiles_public enable row level security;

create policy "anyone can read profiles" on public.profiles_public for select to anon, authenticated
  using (true);
