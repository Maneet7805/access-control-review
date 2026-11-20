drop policy "any update" on public.notes;
create policy "own update" on public.notes for update to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());
