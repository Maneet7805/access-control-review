-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

create table public.notes (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id),
  body text not null
);

insert into public.notes (id, owner_id, body) values
  ('cccccccc-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'note of A'),
  ('cccccccc-0000-0000-0000-000000000002', '22222222-2222-2222-2222-222222222222', 'note of B');

alter table public.notes enable row level security;

create policy "own notes" on public.notes for select to authenticated
  using (owner_id = auth.uid());

-- Fix: runs with the caller's rights (so row security applies) and visitors may not call it.
create function public.note_count() returns bigint
  language sql security invoker set search_path = public as $$
  select count(*) from public.notes;
$$;

revoke execute on function public.note_count() from public, anon;
grant execute on function public.note_count() to authenticated;
