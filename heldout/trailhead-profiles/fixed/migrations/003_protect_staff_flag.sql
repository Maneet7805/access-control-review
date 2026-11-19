revoke update on public.member_profiles from authenticated;
grant update (display_name, bio) on public.member_profiles to authenticated;
