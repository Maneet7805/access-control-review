drop policy "open a ticket" on public.support_requests;
revoke insert on public.support_requests from anon;

create policy "open own ticket" on public.support_requests
  for insert to authenticated with check (requester_id = auth.uid());
