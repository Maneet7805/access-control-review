-- tickets belong to signed-in customers
create type public.ticket_state as enum ('open', 'pending', 'closed');

create table public.support_requests (
  id uuid primary key default gen_random_uuid(),
  requester_id uuid not null references auth.users (id) on delete cascade,
  subject text not null,
  message text not null,
  state public.ticket_state not null default 'open',
  created_at timestamptz not null default now()
);

alter table public.support_requests enable row level security;
grant select, insert on public.support_requests to anon, authenticated;

create policy "open a ticket" on public.support_requests
  for insert to public with check (true);

create policy "see own tickets" on public.support_requests
  for select to authenticated using (requester_id = auth.uid());
