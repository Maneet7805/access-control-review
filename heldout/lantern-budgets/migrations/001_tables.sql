create table public.budgets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  name text not null,
  limit_cents integer not null check (limit_cents >= 0)
);

create table public.budget_lines (
  id uuid primary key default gen_random_uuid(),
  budget_id uuid not null references public.budgets (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  label text not null,
  amount_cents integer not null
);

create index on public.budget_lines (budget_id);
