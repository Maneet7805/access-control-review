insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'pia@trailhead.test'),
  ('22222222-2222-4222-8222-222222222222', 'quin@trailhead.test');

insert into public.member_profiles (user_id, display_name, bio) values
  ('11111111-1111-4111-8111-111111111111', 'Pia', 'Weekend hiker'),
  ('22222222-2222-4222-8222-222222222222', 'Quin', 'Trail runner and volunteer');
