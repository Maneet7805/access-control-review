insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'gil@launch.test'),
  ('22222222-2222-4222-8222-222222222222', 'hana@launch.test');

insert into public.waitlist_entries (email, source) values
  ('first@example.test', 'twitter'),
  ('second@example.test', 'newsletter');

insert into public.early_access_codes (issued_to, code) values
  ('11111111-1111-4111-8111-111111111111', 'EA-ALPHA-1'),
  ('11111111-1111-4111-8111-111111111111', 'EA-ALPHA-2'),
  ('22222222-2222-4222-8222-222222222222', 'EA-BRAVO-1');
