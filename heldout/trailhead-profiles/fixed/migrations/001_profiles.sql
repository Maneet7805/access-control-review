create table public.member_profiles (
  user_id uuid primary key references auth.users (id) on delete cascade,
  display_name text not null,
  bio text,
  is_staff boolean not null default false,
  updated_at timestamptz not null default now()
);

alter table public.member_profiles enable row level security;
grant select, update on public.member_profiles to authenticated;

create policy "own profile readable" on public.member_profiles
  for select to authenticated using (user_id = (select auth.uid()));

create policy "own profile editable" on public.member_profiles
  for update to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));
