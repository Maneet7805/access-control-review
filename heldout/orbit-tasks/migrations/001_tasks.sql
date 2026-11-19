create table public.staff (
  user_id uuid primary key references auth.users (id) on delete cascade
);

create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  title text not null,
  done boolean not null default false,
  updated_at timestamptz not null default now()
);

create index tasks_user_id_idx on public.tasks (user_id);

create function public.set_updated_at() returns trigger
language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger tasks_set_updated_at before update on public.tasks
  for each row execute function public.set_updated_at();
