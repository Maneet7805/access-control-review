insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'quinn@quill.test'),
  ('22222222-2222-4222-8222-222222222222', 'remy@quill.test');

insert into public.journal_entries (author_id, title, body, mood) values
  ('11111111-1111-4111-8111-111111111111', 'First week', 'Settled into the new flat.', 'great'),
  ('11111111-1111-4111-8111-111111111111', 'Bad commute', 'Train cancelled twice.', 'rough'),
  ('22222222-2222-4222-8222-222222222222', 'Garden plans', 'Tomatoes and beans this year.', 'ok'),
  ('22222222-2222-4222-8222-222222222222', 'Job interview', 'Nervous but it went fine.', 'ok');
