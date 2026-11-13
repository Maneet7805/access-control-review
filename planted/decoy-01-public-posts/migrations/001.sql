-- A public blog: everyone, signed in or not, is meant to read the posts. No owner column.
create table public.posts (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  body text not null
);

insert into public.posts (title, body) values
  ('Hello', 'First post'),
  ('News', 'Second post');

alter table public.posts enable row level security;

create policy "anyone can read posts" on public.posts for select to anon, authenticated
  using (true);
