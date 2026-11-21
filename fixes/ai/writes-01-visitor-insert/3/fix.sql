-- Ensure row level security is enabled on "notes".
alter table public.notes enable row level security;

-- Allow only signed-in users to insert rows, and only rows they own.
drop policy if exists "notes_insert_own" on public.notes;

create policy "notes_insert_own"
  on public.notes
  for insert
  to authenticated
  with check (
    auth.uid() is not null
    and owner_id = auth.uid()
  );