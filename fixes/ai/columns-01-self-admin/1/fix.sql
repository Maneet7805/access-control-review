-- Prevent signed-in users from changing "role" on public.members.
-- Table-level UPDATE is revoked, then re-granted only on the other columns,
-- so existing profile edits keep working. Column names are read from the
-- catalog, so none are hard-coded here.

do $$
declare
  cols      text;
  anon_had  boolean := has_table_privilege('anon',          'public.members', 'UPDATE');
  auth_had  boolean := has_table_privilege('authenticated', 'public.members', 'UPDATE');
begin
  select string_agg(quote_ident(attname), ', ' order by attnum)
    into cols
  from pg_attribute
  where attrelid = 'public.members'::regclass
    and attnum > 0
    and not attisdropped
    and attname <> 'role';

  -- Remove table-level update (a column-level revoke alone has no effect
  -- while a table-level grant exists), and any column-level grant on role.
  revoke update on public.members from public, anon, authenticated;
  revoke update (role) on public.members from public, anon, authenticated;

  -- Restore update on every column except "role" for roles that had it before.
  if cols is not null then
    if auth_had then
      execute format('grant update (%s) on public.members to authenticated', cols);
    end if;
    if anon_had then
      execute format('grant update (%s) on public.members to anon', cols);
    end if;
  end if;
end
$$;