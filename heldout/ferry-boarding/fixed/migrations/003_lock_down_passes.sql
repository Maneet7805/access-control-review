alter table public.boarding_passes enable row level security;
revoke select on public.boarding_passes from anon;

create policy "passengers read own passes" on public.boarding_passes
  for select to authenticated
  using (passenger_id = auth.uid());
