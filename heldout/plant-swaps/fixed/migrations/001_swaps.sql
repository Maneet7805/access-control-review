create table public.swap_offers (
  id uuid primary key default gen_random_uuid(),
  offered_by uuid not null references auth.users (id) on delete cascade,
  plant text not null,
  wanted text,
  created_at timestamptz not null default now()
);

alter table public.swap_offers enable row level security;
grant select on public.swap_offers to anon, authenticated;
grant insert, update on public.swap_offers to authenticated;

-- everyone can browse offers
create policy "browse offers" on public.swap_offers for select using (true);

create policy "post offer" on public.swap_offers
  for insert to authenticated with check (offered_by = auth.uid());

-- members can edit an offer or claim it by putting their name on it
create policy "claim or edit offer" on public.swap_offers
  for update to authenticated
  using (auth.uid() is not null)
  with check (offered_by = auth.uid());
