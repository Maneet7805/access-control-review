create or replace function public.spend_points(card_owner uuid, amount integer)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  remaining integer;
begin
  if card_owner is distinct from auth.uid() then
    raise exception 'not your card' using errcode = '42501';
  end if;
  update public.loyalty_cards
     set points = points - amount
   where owner_id = card_owner
  returning points into remaining;
  return remaining;
end;
$$;
