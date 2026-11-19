drop function public.fee_total(uuid);

create function public.fee_total(p_user uuid)
returns bigint
language plpgsql
stable
security definer
set search_path = public
as $$
begin
  if p_user is distinct from auth.uid() then
    raise exception 'not your account' using errcode = '42501';
  end if;
  return (select coalesce(sum(fee_cents), 0) from public.loan_records where borrower_id = p_user);
end;
$$;

revoke execute on function public.fee_total(uuid) from public, anon;
grant execute on function public.fee_total(uuid) to authenticated;
