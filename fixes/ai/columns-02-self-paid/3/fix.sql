-- Stop signed-in users from changing "paid" on public.accounts.
-- Table-level UPDATE is revoked, then re-granted on every column except "paid",
-- so other updates the app makes keep working. The column list is built
-- dynamically, so no other column names are assumed.

do $$
declare
  cols text;
  r text;
begin
  select string_agg(format('%I', a.attname), ', ' order by a.attnum)
    into cols
  from pg_attribute a
  where a.attrelid = 'public.accounts'::regclass
    and a.attnum > 0
    and not a.attisdropped
    and a.attname <> 'paid';

  foreach r in array array['anon', 'authenticated'] loop
    -- remove table-level and any column-level UPDATE on "paid"
    execute format('revoke update on table public.accounts from %I', r);
    execute format('revoke update (paid) on table public.accounts from %I', r);

    -- restore UPDATE on every other column
    if cols is not null then
      execute format('grant update (%s) on table public.accounts to %I', cols, r);
    end if;
  end loop;
end
$$;

-- Also remove any grant made through PUBLIC.
revoke update (paid) on table public.accounts from public;