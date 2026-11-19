-- member directory is public, it is how people find each other
create table public.circle_members (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  nickname text not null,
  joined_on date not null default current_date,
  contact_phone text
);

alter table public.circle_members enable row level security;
grant select on public.circle_members to anon, authenticated;

create policy "directory is public" on public.circle_members
  for select to public using (true);
