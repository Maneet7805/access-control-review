-- Ferry boarding passes: travellers look up their own passes in the app
create table public.boarding_passes (
  id uuid primary key default gen_random_uuid(),
  passenger_id uuid not null references auth.users (id) on delete cascade,
  route text not null,
  seat text,
  departs_at timestamptz not null,
  created_at timestamptz not null default now()
);

create index boarding_passes_passenger_idx on public.boarding_passes (passenger_id);

-- the app only reads passes, so only select is granted
revoke all on public.boarding_passes from anon, authenticated;
grant select on public.boarding_passes to anon, authenticated;
