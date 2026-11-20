-- Negative control: the public columns are revoked too, so visitors can read nothing from the table.
create table public.directory (
  id uuid primary key default gen_random_uuid(),
  display_name text not null,
  phone text
);

insert into public.directory (display_name, phone) values
  ('Member A', '+60 12-000 0001'),
  ('Member B', '+60 12-000 0002');

alter table public.directory enable row level security;

create policy "public profiles" on public.directory for select to anon, authenticated using (true);

revoke select on public.directory from anon, authenticated;
