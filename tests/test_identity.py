import psycopg
import pytest
from conftest import ROOT

from access_review.identity import as_user, as_visitor
from access_review.probes import user_reads_rows
from access_review.sandbox import sandbox

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


@pytest.fixture(scope="module")
def conn_str(tmp_path_factory):
    with sandbox(tmp_path_factory.mktemp("empty"), baseline=True) as connection_string:
        yield connection_string


def _uid_and_role(conn):
    return conn.execute("select auth.uid()::text, current_user").fetchone()


def test_as_user_makes_auth_uid_return_that_user(conn_str):
    with psycopg.connect(conn_str, autocommit=True) as conn:
        as_user(conn, USER_A)
        assert _uid_and_role(conn) == (USER_A, "authenticated")


def test_as_visitor_makes_auth_uid_null(conn_str):
    with psycopg.connect(conn_str, autocommit=True) as conn:
        as_visitor(conn)
        assert _uid_and_role(conn) == (None, "anon")


def test_switching_users_on_one_connection_leaves_nothing_behind(conn_str):
    with psycopg.connect(conn_str, autocommit=True) as conn:
        as_user(conn, USER_A)
        as_user(conn, USER_B)
        assert _uid_and_role(conn) == (USER_B, "authenticated")
        as_visitor(conn)
        assert _uid_and_role(conn) == (None, "anon")


def test_no_identity_without_the_helpers(conn_str):
    # Negative control: a plain connection has no identity, so the helpers are what set it.
    with psycopg.connect(conn_str, autocommit=True) as conn:
        assert conn.execute("select auth.uid()").fetchone()[0] is None


def _owner_policy_app(tmp_path, policy_condition):
    (tmp_path / "001.sql").write_text(f"""
        create table public.notes (owner_id uuid not null, body text not null);
        insert into public.notes values ('{USER_A}', 'a note'), ('{USER_B}', 'b note');
        alter table public.notes enable row level security;
        create policy read_notes on public.notes for select to authenticated using ({policy_condition});
    """)
    return tmp_path


def test_user_probe_sees_only_own_rows_when_policy_checks_auth_uid(tmp_path):
    with sandbox(_owner_policy_app(tmp_path, "owner_id = auth.uid()"), baseline=True) as conn_str:
        assert {str(row["owner_id"]) for row in user_reads_rows(conn_str, "notes", USER_A)} == {USER_A}


def test_user_probe_sees_everyones_rows_when_policy_is_wide_open(tmp_path):
    # Negative control for the probe: the flawed app leaks, so the probe must show both owners.
    with sandbox(_owner_policy_app(tmp_path, "true"), baseline=True) as conn_str:
        assert {str(row["owner_id"]) for row in user_reads_rows(conn_str, "notes", USER_A)} == {USER_A, USER_B}


def test_old_identity_setting_is_gone_from_src():
    files = [p for p in (ROOT / "src").rglob("*") if p.suffix in {".py", ".sql"}]
    offenders = [p.name for p in files if "app.user_id" in p.read_text()]
    assert offenders == []
