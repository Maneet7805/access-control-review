insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'ines@swaps.test'),
  ('22222222-2222-4222-8222-222222222222', 'jonas@swaps.test');

insert into public.swap_offers (offered_by, plant, wanted) values
  ('11111111-1111-4111-8111-111111111111', 'Monstera cutting', 'Any fern'),
  ('11111111-1111-4111-8111-111111111111', 'Spider plant babies', null),
  ('22222222-2222-4222-8222-222222222222', 'Basil seedlings', 'Mint');
