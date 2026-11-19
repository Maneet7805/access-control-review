create type public.slot_status as enum ('held', 'confirmed', 'cancelled');

create table public.kiln_bookings (
  id uuid primary key default gen_random_uuid(),
  booked_by uuid not null references auth.users (id) on delete cascade,
  kiln text not null,
  starts_at timestamptz not null,
  note text,
  status public.slot_status not null default 'held'
);

create index kiln_bookings_start_idx on public.kiln_bookings (starts_at);
alter table public.kiln_bookings enable row level security;

create policy "calendar is shared" on public.kiln_bookings
  for select to authenticated using (true);
create policy "book a slot" on public.kiln_bookings
  for insert to authenticated with check (booked_by = auth.uid());
create policy "edit bookings" on public.kiln_bookings
  for update to authenticated using (true) with check (true);

-- booked_by can never be edited from the client
revoke all on public.kiln_bookings from anon, authenticated;
grant select, insert on public.kiln_bookings to authenticated;
grant update (kiln, starts_at, note, status) on public.kiln_bookings to authenticated;
