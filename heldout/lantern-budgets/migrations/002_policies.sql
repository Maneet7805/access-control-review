alter table public.budgets enable row level security;
alter table public.budget_lines enable row level security;
grant select, insert, update, delete on public.budgets, public.budget_lines to authenticated;

create policy budgets_select on public.budgets
  for select to authenticated using (owner_id = (select auth.uid()));
create policy budgets_insert on public.budgets
  for insert to authenticated with check (owner_id = (select auth.uid()));
create policy budgets_update on public.budgets
  for update to authenticated
  using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));
create policy budgets_delete on public.budgets
  for delete to authenticated using (owner_id = (select auth.uid()));

create policy lines_select on public.budget_lines
  for select to authenticated using (owner_id = (select auth.uid()));
create policy lines_insert on public.budget_lines
  for insert to authenticated
  with check (
    owner_id = (select auth.uid())
    and exists (select 1 from public.budgets b
                where b.id = budget_id and b.owner_id = (select auth.uid()))
  );
create policy lines_update on public.budget_lines
  for update to authenticated
  using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));
create policy lines_delete on public.budget_lines
  for delete to authenticated using (owner_id = (select auth.uid()));
