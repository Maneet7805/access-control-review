-- Two users, as Supabase would hold them. user-a is 1111..., user-b is 2222...
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

-- Meant for admins only, but nothing checks who calls it. Planted flaw (U2): any signed-in user may call it.
create function public.admin_delete_user(target uuid) returns void
  language plpgsql security definer set search_path = public as $$
begin
  delete from auth.users where id = target;
end;
$$;

revoke execute on function public.admin_delete_user(uuid) from public, anon;
grant execute on function public.admin_delete_user(uuid) to authenticated, service_role;
