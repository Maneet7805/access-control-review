drop policy "entries_select_authenticated" on public.journal_entries;

create policy "entries_select_own" on public.journal_entries
  for select to authenticated using (author_id = (select auth.uid()));
