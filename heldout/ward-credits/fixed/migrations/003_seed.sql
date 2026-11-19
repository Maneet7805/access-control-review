insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'zoe@ward.test'),
  ('22222222-2222-4222-8222-222222222222', 'abe@ward.test');

insert into public.credit_accounts (user_id, balance) values
  ('11111111-1111-4111-8111-111111111111', 10),
  ('22222222-2222-4222-8222-222222222222', 25);

insert into public.app_admins (user_id) values ('22222222-2222-4222-8222-222222222222');
