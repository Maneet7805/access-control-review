-- total fees for the account page
create function public.fee_total(p_user uuid)
returns bigint
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(sum(fee_cents), 0) from public.loan_records where borrower_id = p_user;
$$;
