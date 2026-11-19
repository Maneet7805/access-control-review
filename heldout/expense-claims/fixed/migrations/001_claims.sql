create table public.expense_claims (
  id uuid primary key default gen_random_uuid(),
  claimant_id uuid not null references auth.users (id) on delete cascade,
  merchant text not null,
  amount_cents integer not null check (amount_cents > 0),
  status text not null default 'submitted'
);

alter table public.expense_claims enable row level security;
grant select, insert on public.expense_claims to authenticated;

create policy "claimant reads own" on public.expense_claims
  for select to authenticated using (claimant_id = auth.uid());
create policy "claimant files own" on public.expense_claims
  for insert to authenticated with check (claimant_id = auth.uid());
