revoke select on public.circle_members from anon, authenticated;
grant select (id, user_id, nickname, joined_on) on public.circle_members to anon, authenticated;
