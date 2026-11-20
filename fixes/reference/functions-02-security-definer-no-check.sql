create or replace function public.set_note_body(note_id uuid, new_body text) returns void
  language plpgsql security definer set search_path = public as $$
begin
  if not exists (select 1 from public.notes where id = note_id and owner_id = auth.uid()) then
    raise exception 'not your note';
  end if;
  update public.notes set body = new_body where id = note_id;
end;
$$;
