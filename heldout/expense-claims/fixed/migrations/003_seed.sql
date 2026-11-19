insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'vera@expense.test'),
  ('22222222-2222-4222-8222-222222222222', 'will@expense.test');

insert into public.expense_claims (claimant_id, merchant, amount_cents, status) values
  ('11111111-1111-4111-8111-111111111111', 'Rail Co', 4520, 'submitted'),
  ('11111111-1111-4111-8111-111111111111', 'Cafe Nero', 880, 'approved'),
  ('22222222-2222-4222-8222-222222222222', 'Hotel Aster', 21000, 'submitted');
