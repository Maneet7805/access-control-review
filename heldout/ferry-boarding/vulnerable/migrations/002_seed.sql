insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'ana@ferry.test'),
  ('22222222-2222-4222-8222-222222222222', 'ben@ferry.test');

insert into public.boarding_passes (passenger_id, route, seat, departs_at) values
  ('11111111-1111-4111-8111-111111111111', 'Harbour - North Isle', '12A', '2026-07-01 08:00+00'),
  ('11111111-1111-4111-8111-111111111111', 'North Isle - Harbour', '12B', '2026-07-03 17:30+00'),
  ('22222222-2222-4222-8222-222222222222', 'Harbour - South Isle', '4C', '2026-07-02 09:15+00'),
  ('22222222-2222-4222-8222-222222222222', 'South Isle - Harbour', '4D', '2026-07-04 16:00+00');
