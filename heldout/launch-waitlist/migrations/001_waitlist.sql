-- landing page signup form: anyone may add an email, nobody may read the list
create table public.waitlist_entries (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  source text,
  created_at timestamptz not null default now()
);

create unique index waitlist_entries_email_idx on public.waitlist_entries (lower(email));

alter table public.waitlist_entries enable row level security;
revoke all on public.waitlist_entries from anon, authenticated;
grant insert on public.waitlist_entries to anon, authenticated;

create policy "join the waitlist" on public.waitlist_entries
  for insert to anon, authenticated with check (true);
