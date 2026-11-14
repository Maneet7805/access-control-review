-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

-- Fix: only the server-side service role may call it. Signed-in users and visitors get "permission denied".
create function public.admin_delete_user(target uuid) returns void
  language plpgsql security definer set search_path = public as $$
begin
  delete from auth.users where id = target;
end;
$$;

revoke execute on function public.admin_delete_user(uuid) from public, anon, authenticated;
grant execute on function public.admin_delete_user(uuid) to service_role;
