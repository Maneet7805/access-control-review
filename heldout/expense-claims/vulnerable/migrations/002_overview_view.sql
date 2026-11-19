-- dashboard view for the claims screen
create view public.claim_overview as
  select id, claimant_id, merchant, amount_cents, status
  from public.expense_claims;

revoke all on public.claim_overview from anon, authenticated;
grant select on public.claim_overview to authenticated;
