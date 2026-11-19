insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'rex@orbit.test'),
  ('22222222-2222-4222-8222-222222222222', 'sia@orbit.test');

insert into public.staff (user_id) values ('22222222-2222-4222-8222-222222222222');

insert into public.tasks (user_id, title, done) values
  ('11111111-1111-4111-8111-111111111111', 'Book dentist', false),
  ('11111111-1111-4111-8111-111111111111', 'Renew passport', true),
  ('22222222-2222-4222-8222-222222222222', 'Review weekly report', false);
