insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'tess@circle.test'),
  ('22222222-2222-4222-8222-222222222222', 'uma@circle.test');

insert into public.circle_members (user_id, nickname, joined_on, contact_phone) values
  ('11111111-1111-4111-8111-111111111111', 'tess_t', '2025-09-01', '555-0101'),
  ('22222222-2222-4222-8222-222222222222', 'umami', '2025-10-12', '555-0102');
