insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111', 'kai@rind.test'),
  ('22222222-2222-4222-8222-222222222222', 'lena@rind.test');

insert into public.recipes (author_id, title, method, is_published) values
  ('11111111-1111-4111-8111-111111111111', 'Lemon curd', 'Whisk, heat, strain.', true),
  ('11111111-1111-4111-8111-111111111111', 'Secret chilli', 'Draft: still testing the heat.', false),
  ('22222222-2222-4222-8222-222222222222', 'Flatbreads', 'Mix, rest, fry.', true),
  ('22222222-2222-4222-8222-222222222222', 'Sourdough notes', 'Draft: hydration too low.', false);
