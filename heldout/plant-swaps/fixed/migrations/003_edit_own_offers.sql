drop policy "claim or edit offer" on public.swap_offers;

create policy "edit own offer" on public.swap_offers
  for update to authenticated
  using (offered_by = auth.uid())
  with check (offered_by = auth.uid());
