create type public.mood as enum ('great', 'ok', 'rough');

create table public.journal_entries (
  id uuid primary key default gen_random_uuid(),
  author_id uuid not null references auth.users (id) on delete cascade,
  title text not null,
  body text not null default '',
  mood public.mood not null default 'ok',
  created_at timestamptz not null default now()
);

create index on public.journal_entries (author_id, created_at desc);

alter table public.journal_entries enable row level security;
grant select, insert, update, delete on public.journal_entries to authenticated;
