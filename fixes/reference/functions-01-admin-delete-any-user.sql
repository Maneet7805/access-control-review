revoke execute on function public.admin_delete_user(uuid) from public, anon, authenticated;
grant execute on function public.admin_delete_user(uuid) to service_role;
