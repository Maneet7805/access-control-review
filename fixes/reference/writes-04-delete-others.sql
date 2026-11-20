drop policy "any delete" on public.notes;
create policy "own delete" on public.notes for delete to authenticated
  using (owner_id = auth.uid());
