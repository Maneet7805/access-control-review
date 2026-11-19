create view public.budget_totals
with (security_invoker = true) as
  select b.id as budget_id, b.owner_id, b.name,
         coalesce(sum(l.amount_cents), 0)::bigint as spent_cents
  from public.budgets b
  left join public.budget_lines l on l.budget_id = b.id
  group by b.id;

revoke all on public.budget_totals from anon;
grant select on public.budget_totals to authenticated;

create function public.rename_budget(b_id uuid, new_name text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.budgets set name = new_name where id = b_id and owner_id = auth.uid();
  if not found then
    raise exception 'budget not found' using errcode = '42501';
  end if;
end;
$$;

revoke execute on function public.rename_budget(uuid, text) from public, anon;
grant execute on function public.rename_budget(uuid, text) to authenticated;
