insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'ida@library.test'),
  ('22222222-2222-4222-8222-222222222222', 'jack@library.test');

insert into public.loan_records (borrower_id, title, fee_cents, returned) values
  ('11111111-1111-4111-8111-111111111111', 'Dune', 150, true),
  ('11111111-1111-4111-8111-111111111111', 'Emma', 300, false),
  ('22222222-2222-4222-8222-222222222222', 'Ulysses', 900, false);
