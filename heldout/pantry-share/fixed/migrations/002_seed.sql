insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'lia@pantry.test'),
  ('22222222-2222-4222-8222-222222222222', 'omar@pantry.test');

insert into public.pantry_items (owner_id, item, qty, best_before) values
  ('11111111-1111-4111-8111-111111111111', 'Rice 1kg', 2, '2027-01-31'),
  ('11111111-1111-4111-8111-111111111111', 'Lentils', 3, '2026-12-15'),
  ('22222222-2222-4222-8222-222222222222', 'Tinned tomatoes', 6, '2027-03-01');
