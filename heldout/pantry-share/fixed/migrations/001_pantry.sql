-- community pantry: anyone can browse what is on the shelf
create table public.pantry_items (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  item text not null,
  qty integer not null default 1 check (qty >= 0),
  best_before date
);

alter table public.pantry_items enable row level security;

grant select on public.pantry_items to anon, authenticated;
grant insert, update, delete on public.pantry_items to authenticated;

create policy "browse shelf" on public.pantry_items
  for select to anon, authenticated using (true);
create policy "add item" on public.pantry_items
  for insert to authenticated with check (owner_id = auth.uid());
create policy "adjust own item" on public.pantry_items
  for update to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "tidy up" on public.pantry_items
  for delete to authenticated using (true);
