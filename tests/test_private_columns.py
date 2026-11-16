"""M3.5: a private column (phone, ssn ...) that visitors or other users can read (C2)."""
import json

import pytest
from conftest import PLANTED

from access_review.cli import main
from access_review.evidence import Evidence
from access_review.identity import as_visitor
from access_review.probes import user_reads_private_columns, visitor_reads_private_columns
from access_review.rules import private_column_read
from access_review.sandbox import sandbox

ANSWER_KEY = json.loads((PLANTED / "answer_key.json").read_text())
APP = "columns-03-phone-exposed"
VARIANTS = ["vulnerable", "fixed"]
USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


def _planted(variant):
    return any(f["flaw_id"] == "C2" and f["table"] == "directory" and f["column"] == "phone"
               for f in ANSWER_KEY[APP][f"flaws_{variant}"])


@pytest.mark.parametrize("variant", VARIANTS)
def test_private_column_probes_match_answer_key(variant):
    with sandbox(PLANTED / APP / variant / "migrations", baseline=True) as box:
        visitor = visitor_reads_private_columns(box, "directory", None)
        user = user_reads_private_columns(box, "directory", None, USER_A)
    for found in (visitor, user):
        assert [column for column, _ in found] == ["phone"]
        evidence = found[0][1]
        assert bool(evidence.rows_seen) == _planted(variant)
        assert evidence.result == ("ok" if _planted(variant) else "permission_denied")


def test_the_fixed_twin_still_shows_the_public_columns():
    # Allowed access: the fix must not hide the public part of the profile page.
    with sandbox(PLANTED / APP / "fixed" / "migrations", baseline=True) as box:
        assert box.run(as_visitor() + "SELECT count(display_name) FROM public.directory;").splitlines()[-1] == "2"


def test_a_table_with_no_private_column_gives_nothing_to_test():
    # Negative control: notes has no column named like phone, ssn or password.
    with sandbox(PLANTED / "writes-03-update-others" / "vulnerable" / "migrations", baseline=True) as box:
        assert visitor_reads_private_columns(box, "notes", "owner_id") == []
        assert user_reads_private_columns(box, "notes", "owner_id", USER_A) == []


def test_a_private_column_next_to_an_owner_column_returns_both(tmp_path):
    (tmp_path / "001.sql").write_text(
        "insert into auth.users (id, email) values ('11111111-1111-1111-1111-111111111111', 'a@example.test');"
        "create table public.people (id uuid primary key default gen_random_uuid(),"
        " user_id uuid not null references auth.users (id), home_phone text);"
        "insert into public.people (user_id, home_phone) values ('11111111-1111-1111-1111-111111111111', '123');"
        "alter table public.people enable row level security;"
        "create policy s on public.people for select to authenticated using (user_id = auth.uid());")
    with sandbox(tmp_path, baseline=True) as box:
        user = dict(user_reads_private_columns(box, "people", "user_id", USER_A))["home_phone"]
        visitor = dict(visitor_reads_private_columns(box, "people", "user_id"))["home_phone"]
    assert user.rows_seen == [{"home_phone": "123", "user_id": USER_A}] and visitor.rows_seen == []


def _read(actor, rows, result="ok"):
    probe = "visitor_reads_private_column" if actor == "visitor" else "user_reads_private_column"
    return Evidence(probe, actor, "SELECT", result, rows)


def test_a_visitor_reading_a_private_value_is_proved_c2():
    finding = private_column_read("directory", "phone", None, _read("visitor", [{"phone": "1"}]))
    assert (finding.flaw_id, finding.status, finding.table, finding.column) == ("C2", "proved", "directory", "phone")


def test_a_user_reading_another_users_private_value_is_proved_c2():
    rows = [{"phone": "1", "user_id": USER_A}, {"phone": "2", "user_id": USER_B}]
    assert private_column_read("people", "phone", "user_id", _read(f"user:{USER_A}", rows)).flaw_id == "C2"


def test_no_c2_for_own_rows_nothing_empty_values_or_a_refusal():
    actor = f"user:{USER_A}"
    assert private_column_read("people", "phone", "user_id", _read(actor, [{"phone": "1", "user_id": USER_A}])) is None
    assert private_column_read("people", "phone", "user_id", _read(actor, [])) is None
    assert private_column_read("directory", "phone", None, _read("visitor", [{"phone": None}])) is None
    assert private_column_read("directory", "phone", None, _read("visitor", [], "permission_denied")) is None
    assert private_column_read("directory", "phone", None, Evidence("visitor_reads_rows", "visitor", "S", "ok",
                                                                    [{"phone": "1"}])) is None


def test_a_signed_in_user_with_no_owner_column_sees_every_value_as_not_theirs():
    assert private_column_read("directory", "phone", None, _read(f"user:{USER_A}", [{"phone": "1"}])) is not None


def test_review_finds_the_planted_column_and_the_fixed_twin_is_clean(tmp_path):
    out = tmp_path / "report.md"
    assert main(["review", str(PLANTED / APP / "vulnerable" / "migrations"), "--out", str(out)]) == 1
    report = out.read_text(encoding="utf-8")
    assert report.count("\n## ") == 2 and 'can read the private column "phone"' in report
    assert "Proved" in report and "Needs your decision" in report  # C2 proved, R1 for the public-by-design table
    assert main(["review", str(PLANTED / APP / "fixed" / "migrations"), "--out", str(out)]) == 0
    assert "No violation found under this test." in out.read_text(encoding="utf-8")
