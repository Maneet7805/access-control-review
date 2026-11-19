create table public.credit_accounts (
  user_id uuid primary key references auth.users (id) on delete cascade,
  balance integer not null default 0
);

create table public.app_admins (
  user_id uuid primary key references auth.users (id) on delete cascade
);

alter table public.credit_accounts enable row level security;
alter table public.app_admins enable row level security;
grant select on public.credit_accounts to authenticated;

create policy "see own balance" on public.credit_accounts
  for select to authenticated using (user_id = auth.uid());
