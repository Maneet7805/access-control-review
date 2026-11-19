insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'mara@kiln.test'),
  ('22222222-2222-4222-8222-222222222222', 'noel@kiln.test');

insert into public.kiln_bookings (booked_by, kiln, starts_at, note) values
  ('11111111-1111-4111-8111-111111111111', 'Large electric', '2026-08-10 09:00+00', 'Bisque firing'),
  ('11111111-1111-4111-8111-111111111111', 'Large electric', '2026-08-12 09:00+00', 'Glaze firing'),
  ('22222222-2222-4222-8222-222222222222', 'Raku kiln', '2026-08-11 14:00+00', 'Raku demo');
