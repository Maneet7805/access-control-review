import pytest
from conftest import ROOT

from access_review.identity import as_user, as_visitor
from access_review.probes import user_reads_rows
from access_review.sandbox import sandbox

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


@pytest.fixture(scope="module")
def box(tmp_path_factory):
    with sandbox(tmp_path_factory.mktemp("empty"), baseline=True) as running:
        yield running


UID_AND_ROLE = "select coalesce(auth.uid()::text, 'null') || '|' || current_user"


def test_as_user_makes_auth_uid_return_that_user(box):
    assert box.run(as_user(USER_A) + UID_AND_ROLE) == f"{USER_A}|authenticated"


def test_as_visitor_makes_auth_uid_null(box):
    assert box.run(as_visitor() + UID_AND_ROLE) == "null|anon"


def test_switching_users_in_one_session_leaves_nothing_behind(box):
    assert box.run(as_user(USER_A) + as_user(USER_B) + UID_AND_ROLE) == f"{USER_B}|authenticated"
    assert box.run(as_user(USER_A) + as_visitor() + UID_AND_ROLE) == "null|anon"


def test_no_identity_without_the_helpers(box):
    # Negative control: a plain session has no identity, so the helpers are what set it.
    assert box.run("select auth.uid() is null") == "t"


def test_user_id_must_be_a_uuid():
    with pytest.raises(ValueError):
        as_user("x'; drop table notes; --")


def _owner_policy_app(tmp_path, policy_condition):
    (tmp_path / "001.sql").write_text(f"""
        create table public.notes (owner_id uuid not null, body text not null);
        insert into public.notes values ('{USER_A}', 'a note'), ('{USER_B}', 'b note');
        alter table public.notes enable row level security;
        create policy read_notes on public.notes for select to authenticated using ({policy_condition});
    """)
    return tmp_path


def test_user_probe_sees_only_own_rows_when_policy_checks_auth_uid(tmp_path):
    with sandbox(_owner_policy_app(tmp_path, "owner_id = auth.uid()"), baseline=True) as box:
        assert {row["owner_id"] for row in user_reads_rows(box, "notes", USER_A).rows_seen} == {USER_A}


def test_user_probe_sees_everyones_rows_when_policy_is_wide_open(tmp_path):
    # Negative control for the probe: the flawed app leaks, so the probe must show both owners.
    with sandbox(_owner_policy_app(tmp_path, "true"), baseline=True) as box:
        assert {row["owner_id"] for row in user_reads_rows(box, "notes", USER_A).rows_seen} == {USER_A, USER_B}


def test_old_identity_setting_is_gone_from_src():
    files = [p for p in (ROOT / "src").rglob("*") if p.suffix in {".py", ".sql"}]
    offenders = [p.name for p in files if "app.user_id" in p.read_text()]
    assert offenders == []
