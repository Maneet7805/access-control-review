-- called from the checkout screen
create function public.spend_points(card_owner uuid, amount integer)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  remaining integer;
begin
  update public.loyalty_cards
     set points = points - amount
   where owner_id = card_owner
  returning points into remaining;
  return remaining;
end;
$$;

revoke execute on function public.spend_points(uuid, integer) from public, anon;
grant execute on function public.spend_points(uuid, integer) to authenticated;
