create table public.early_access_codes (
  id uuid primary key default gen_random_uuid(),
  issued_to uuid not null references auth.users (id) on delete cascade,
  code text not null unique,
  redeemed boolean not null default false
);

alter table public.early_access_codes enable row level security;
grant select on public.early_access_codes to authenticated;

create policy "see own codes" on public.early_access_codes
  for select to authenticated using (issued_to = auth.uid());
