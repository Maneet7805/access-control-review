-- recipes are public once published, drafts stay with the author
create table public.recipes (
  id uuid primary key default gen_random_uuid(),
  author_id uuid not null references auth.users (id) on delete cascade,
  title text not null,
  method text not null,
  is_published boolean not null default false
);

alter table public.recipes enable row level security;
grant select on public.recipes to anon, authenticated;
grant insert, update, delete on public.recipes to authenticated;

create policy "published or mine" on public.recipes
  for select to public
  using (is_published or author_id = (select auth.uid()));

create policy "write own recipes" on public.recipes
  for all to authenticated
  using (author_id = (select auth.uid()))
  with check (author_id = (select auth.uid()));
