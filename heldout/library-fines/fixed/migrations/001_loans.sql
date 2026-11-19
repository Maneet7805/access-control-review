create table public.loan_records (
  id uuid primary key default gen_random_uuid(),
  borrower_id uuid not null references auth.users (id) on delete cascade,
  title text not null,
  fee_cents integer not null default 0,
  returned boolean not null default false
);

alter table public.loan_records enable row level security;
grant select on public.loan_records to authenticated;

create policy "borrowers see own loans" on public.loan_records
  for select to authenticated using (borrower_id = auth.uid());
