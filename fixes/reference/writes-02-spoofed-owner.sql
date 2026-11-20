drop policy "any insert" on public.notes;
create policy "own insert" on public.notes for insert to authenticated
  with check (owner_id = auth.uid());
