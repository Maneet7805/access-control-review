alter table public.profiles enable row level security;

create policy "own profile" on public.profiles for select to authenticated
  using (owner_id = auth.uid());
