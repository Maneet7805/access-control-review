import subprocess

import psycopg
import pytest

from access_review.sandbox import sandbox

# Four migrations that mimic what AI tools write for Supabase apps.
FIXTURES = {
    "001_table.sql": """
        create table public.notes (
            id bigint generated always as identity primary key,
            user_id uuid not null references auth.users(id),
            body text not null
        );
        alter table public.notes enable row level security;
    """,
    "002_policy.sql": """
        create policy "own notes" on public.notes for select to authenticated
            using (user_id = auth.uid());
    """,
    "003_trigger.sql": """
        create table public.profiles (id uuid primary key references auth.users(id));
        create function public.handle_new_user() returns trigger language plpgsql
            security definer set search_path = public as $$
        begin
            insert into public.profiles (id) values (new.id);
            return new;
        end $$;
        create trigger on_auth_user_created after insert on auth.users
            for each row execute function public.handle_new_user();
    """,
    "004_definer_function.sql": """
        create function public.note_count() returns bigint language sql
            security definer set search_path = public as $$ select count(*) from public.notes $$;
        create table public.open_table (id int);
        insert into public.open_table values (1), (2);
    """,
}
USER_A = "11111111-1111-1111-1111-111111111111"


@pytest.fixture(scope="module")
def migrations(tmp_path_factory):
    folder = tmp_path_factory.mktemp("fixture_migrations")
    for name, sql in FIXTURES.items():
        (folder / name).write_text(sql)
    return folder


@pytest.fixture(scope="module")
def conn_str(migrations):
    with sandbox(migrations, baseline=True) as connection_string:
        yield connection_string


def test_four_typical_migrations_apply_on_the_baseline(conn_str):
    with psycopg.connect(conn_str) as conn:
        assert conn.execute("select count(*) from public.notes").fetchone()[0] == 0


def test_trigger_on_auth_users_fires(conn_str):
    with psycopg.connect(conn_str) as conn:
        conn.execute("insert into auth.users (id) values (%s)", (USER_A,))
        assert conn.execute("select count(*) from public.profiles").fetchone()[0] == 1


def test_auth_functions_read_request_jwt_claims(conn_str):
    with psycopg.connect(conn_str) as conn:
        conn.execute("select set_config('request.jwt.claims', %s, false)",
                     (f'{{"sub": "{USER_A}", "role": "authenticated"}}',))
        row = conn.execute("select auth.uid()::text, auth.role(), auth.jwt() ->> 'sub'").fetchone()
        assert row == (USER_A, "authenticated", USER_A)
        conn.execute("select set_config('request.jwt.claims', '', false)")
        assert conn.execute("select auth.uid()").fetchone()[0] is None


def test_table_without_row_security_is_open_to_anon_and_authenticated(conn_str):
    with psycopg.connect(conn_str) as conn:
        for role in ("anon", "authenticated"):
            conn.execute(f"set role {role}")  # noqa: S608 - fixed role names
            assert conn.execute("select count(*) from public.open_table").fetchone()[0] == 2
            conn.execute("reset role")


def test_roles_have_their_real_attributes(conn_str):
    with psycopg.connect(conn_str) as conn:
        rows = dict(conn.execute(
            "select rolname, rolbypassrls from pg_roles where rolname in ('anon','authenticated','service_role')"
        ).fetchall())
        assert rows == {"anon": False, "authenticated": False, "service_role": True}


def test_same_migrations_fail_on_bare_postgres(migrations):
    # Negative control: without the baseline there is no auth schema, so the fixtures cannot apply.
    with pytest.raises(subprocess.CalledProcessError), sandbox(migrations):
        pass
