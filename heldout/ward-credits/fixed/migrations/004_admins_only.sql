create or replace function public.admin_grant_credits(target uuid, delta integer)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  -- the service role has no uid; every signed-in caller must be an admin
  if auth.uid() is not null
     and not exists (select 1 from public.app_admins where user_id = auth.uid()) then
    raise exception 'admins only' using errcode = '42501';
  end if;
  if target is null then
    raise exception 'target required';
  end if;
  update public.credit_accounts set balance = balance + delta where user_id = target;
end;
$$;
