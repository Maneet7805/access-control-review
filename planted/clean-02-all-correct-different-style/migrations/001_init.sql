-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

-- Same protection as clean-01, written another way: one policy for every action, the cached
-- (select auth.uid()) form, a view that applies the reader's rights, and a function that does too.
create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  created_by uuid not null references auth.users (id),
  title text not null,
  done boolean not null default false
);

insert into public.tasks (created_by, title) values
  ('11111111-1111-1111-1111-111111111111', 'task of A'),
  ('22222222-2222-2222-2222-222222222222', 'task of B');

alter table public.tasks enable row level security;

create policy "own tasks" on public.tasks for all to authenticated
  using ((select auth.uid()) = created_by) with check ((select auth.uid()) = created_by);

create view public.my_tasks with (security_invoker = true) as
  select id, created_by, title, done from public.tasks;

create function public.count_tasks() returns bigint language sql security invoker as
  $$ select count(*) from public.tasks $$;
revoke execute on function public.count_tasks() from public, anon;
grant execute on function public.count_tasks() to authenticated;
