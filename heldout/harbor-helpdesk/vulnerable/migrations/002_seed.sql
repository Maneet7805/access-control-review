insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'cass@harbor.test'),
  ('22222222-2222-4222-8222-222222222222', 'dev@harbor.test');

insert into public.support_requests (requester_id, subject, message, state) values
  ('11111111-1111-4111-8111-111111111111', 'Invoice missing', 'I did not get my March invoice.', 'open'),
  ('11111111-1111-4111-8111-111111111111', 'Change email', 'Please update my contact address.', 'closed'),
  ('22222222-2222-4222-8222-222222222222', 'Login loop', 'The login page keeps reloading.', 'pending');
