-- Negative control: the owner's own insert, update, delete and function calls are all blocked.
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

create table public.notes (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id),
  body text not null
);

insert into public.notes (id, owner_id, body) values
  ('cccccccc-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'note of A'),
  ('cccccccc-0000-0000-0000-000000000002', '22222222-2222-2222-2222-222222222222', 'note of B');

alter table public.notes enable row level security;

create policy "own notes" on public.notes for select to authenticated using (owner_id = auth.uid());
create policy "no insert" on public.notes for insert to authenticated with check (false);
create policy "no update" on public.notes for update to authenticated using (false);
create policy "no delete" on public.notes for delete to authenticated using (false);

create function public.set_note_body(note_id uuid, new_body text) returns void
  language plpgsql security definer set search_path = public as $$
begin
  update public.notes set body = new_body where id = note_id and owner_id = auth.uid();
end;
$$;
create function public.note_count() returns bigint
  language sql security invoker set search_path = public as $$
  select count(*) from public.notes;
$$;
create function public.admin_delete_user(target uuid) returns void
  language plpgsql security definer set search_path = public as $$
begin
  delete from auth.users where id = target;
end;
$$;

revoke execute on function public.set_note_body(uuid, text) from public, anon, authenticated;
revoke execute on function public.note_count() from public, anon, authenticated;
revoke execute on function public.admin_delete_user(uuid) from public, anon, authenticated, service_role;
