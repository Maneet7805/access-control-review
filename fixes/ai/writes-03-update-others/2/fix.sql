-- Migration: restrict UPDATE on public.notes to the row owner

alter table public.notes enable row level security;

-- Remove existing UPDATE-only policies on notes (one may have a condition that
-- is always true, e.g. USING (true)). Policies for other commands are untouched.
do $$
declare
  p record;
begin
  for p in
    select policyname
    from pg_policies
    where schemaname = 'public'
      and tablename  = 'notes'
      and cmd        = 'UPDATE'
  loop
    execute format('drop policy if exists %I on public.notes', p.policyname);
  end loop;
end
$$;

drop policy if exists notes_update_own on public.notes;
drop policy if exists notes_update_owner_only on public.notes;

-- Owners can update their own notes, and the changed row must still be theirs.
create policy notes_update_own
  on public.notes
  as permissive
  for update
  to authenticated
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

-- Safety net: a restrictive policy is ANDed with every permissive policy,
-- including any FOR ALL policy that is always true and would otherwise still
-- allow anyone to update, or to reassign owner_id.
create policy notes_update_owner_only
  on public.notes
  as restrictive
  for update
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());