drop policy "tidy up" on public.pantry_items;

create policy "remove own item" on public.pantry_items
  for delete to authenticated using (owner_id = auth.uid());
