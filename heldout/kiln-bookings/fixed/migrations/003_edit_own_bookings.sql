drop policy "edit bookings" on public.kiln_bookings;

create policy "edit own bookings" on public.kiln_bookings
  for update to authenticated
  using (booked_by = auth.uid())
  with check (booked_by = auth.uid());
