-- logged in users can read entries (feed screen)
create policy "entries_select_authenticated" on public.journal_entries
  for select to authenticated using (true);

create policy "entries_insert_own" on public.journal_entries
  for insert to authenticated with check (author_id = (select auth.uid()));

create policy "entries_update_own" on public.journal_entries
  for update to authenticated
  using (author_id = (select auth.uid()))
  with check (author_id = (select auth.uid()));

create policy "entries_delete_own" on public.journal_entries
  for delete to authenticated using (author_id = (select auth.uid()));
