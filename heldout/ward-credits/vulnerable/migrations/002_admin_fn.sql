-- admin dashboard: top up a customer's credits
create function public.admin_grant_credits(target uuid, delta integer)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if target is null then
    raise exception 'target required';
  end if;
  update public.credit_accounts set balance = balance + delta where user_id = target;
end;
$$;

revoke execute on function public.admin_grant_credits(uuid, integer) from public, anon;
grant execute on function public.admin_grant_credits(uuid, integer) to authenticated, service_role;
