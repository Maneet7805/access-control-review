create table public.loyalty_cards (
  owner_id uuid primary key references auth.users (id) on delete cascade,
  points integer not null default 0 check (points >= 0),
  tier text not null default 'bronze'
);

alter table public.loyalty_cards enable row level security;
grant select on public.loyalty_cards to authenticated;

create policy "own card" on public.loyalty_cards
  for select to authenticated using (owner_id = auth.uid());
