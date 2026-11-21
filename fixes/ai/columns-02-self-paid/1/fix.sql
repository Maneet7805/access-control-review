-- Stop signed-in users from updating accounts.paid.
-- Other columns stay updatable by users, so the app keeps working.
-- service_role and security-definer functions are unaffected, so server-side code can still set "paid".

begin;

-- 1. Remove table-level UPDATE (which implicitly covers "paid") from client roles,
--    and explicitly remove any column-level UPDATE on "paid".
revoke update on table public.accounts from authenticated, anon;
revoke update (paid) on table public.accounts from authenticated, anon;

-- 2. Re-grant UPDATE to the signed-in role on every column except "paid".
--    Columns are looked up dynamically so no other column names need to be assumed.
do $$
declare
  cols text;
begin
  select string_agg(quote_ident(column_name), ', ' order by ordinal_position)
    into cols
  from information_schema.columns
  where table_schema = 'public'
    and table_name   = 'accounts'
    and column_name <> 'paid';

  if cols is not null then
    execute format(
      'grant update (%s) on table public.accounts to authenticated',
      cols
    );
  end if;
end
$$;

commit;