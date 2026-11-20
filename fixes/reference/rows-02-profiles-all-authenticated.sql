drop policy "any signed-in user" on public.profiles;
create policy "own profile" on public.profiles for select to authenticated
  using (owner_id = auth.uid());
