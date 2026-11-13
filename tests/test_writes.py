import json

import pytest
from conftest import PLANTED

from access_review.cli import main
from access_review.evidence import Evidence
from access_review.probes import user_inserts_row_for_other, visitor_inserts_row
from access_review.rules import insert_accepted
from access_review.sandbox import sandbox

ANSWER_KEY = json.loads((PLANTED / "answer_key.json").read_text())
APPS = [app for app, entry in ANSWER_KEY.items() if any(i["action"] == "insert" for i in entry["allowed"])]
VARIANTS = [(app, variant) for app in APPS for variant in ("vulnerable", "fixed")]
USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


def _planted(app, variant, flaw_id):
    return any(f["flaw_id"] == flaw_id for f in ANSWER_KEY[app][f"flaws_{variant}"])


@pytest.mark.parametrize("app,variant", VARIANTS)
def test_insert_probes_match_answer_key(app, variant):
    with sandbox(PLANTED / app / variant / "migrations", baseline=True) as box:
        visitor = visitor_inserts_row(box, "notes", "owner_id", USER_A)
        spoof = user_inserts_row_for_other(box, "notes", "owner_id", USER_A, USER_B)
    assert bool(visitor.rows_seen) == _planted(app, variant, "R3")
    assert bool(spoof.rows_seen) == _planted(app, variant, "R4")


@pytest.mark.parametrize("app,variant", VARIANTS)
def test_the_test_rows_are_rolled_back(app, variant):
    with sandbox(PLANTED / app / variant / "migrations", baseline=True) as box:
        visitor_inserts_row(box, "notes", "owner_id", USER_A)
        user_inserts_row_for_other(box, "notes", "owner_id", USER_A, USER_B)
        assert box.run("select count(*) from public.notes") == "2"


@pytest.mark.parametrize("app", APPS)
def test_a_user_can_still_add_a_row_for_themselves_in_the_fixed_twin(app):
    # Allowed access: the fix must not lock the owner out of adding their own rows.
    with sandbox(PLANTED / app / "fixed" / "migrations", baseline=True) as box:
        own = user_inserts_row_for_other(box, "notes", "owner_id", USER_A, USER_A)
    assert own.result == "ok" and [row["owner_id"] for row in own.rows_seen] == [USER_A]


def test_a_refused_insert_is_recorded_as_permission_denied():
    with sandbox(PLANTED / "writes-01-visitor-insert" / "fixed" / "migrations", baseline=True) as box:
        refused = visitor_inserts_row(box, "notes", "owner_id", USER_A)
    assert (refused.result, refused.rows_seen) == ("permission_denied", [])
    assert "row-level security" in refused.error


def test_a_column_type_we_cannot_fill_is_an_error_not_a_finding(tmp_path):
    (tmp_path / "001.sql").write_text("create table public.places (id int primary key, spot point not null);")
    with sandbox(tmp_path, baseline=True) as box:
        evidence = visitor_inserts_row(box, "places", None, USER_A)
    assert evidence.result == "error" and "point" in evidence.error
    assert insert_accepted("places", None, evidence) is None


def _visitor(rows, result="ok"):
    return Evidence("visitor_inserts_row", "visitor", "INSERT", result, rows)


def test_visitor_insert_on_owned_table_is_proved_r3():
    finding = insert_accepted("notes", "owner_id", _visitor([{"owner_id": USER_A}]))
    assert (finding.flaw_id, finding.status, finding.table) == ("R3", "proved", "notes")


def test_visitor_insert_on_table_without_owner_needs_a_decision():
    finding = insert_accepted("signups", None, _visitor([{"id": 1}]))
    assert (finding.flaw_id, finding.status) == ("R3", "needs_decision")


def test_user_inserting_for_someone_else_is_proved_r4_but_for_themselves_is_not():
    other = Evidence("user_inserts_row_for_other", f"user:{USER_A}", "INSERT", "ok", [{"owner_id": USER_B}])
    own = Evidence("user_inserts_row_for_other", f"user:{USER_A}", "INSERT", "ok", [{"owner_id": USER_A}])
    assert insert_accepted("notes", "owner_id", other).flaw_id == "R4"
    assert insert_accepted("notes", "owner_id", own) is None


def test_refused_or_empty_inserts_give_no_finding():
    assert insert_accepted("notes", "owner_id", _visitor([], "permission_denied")) is None
    assert insert_accepted("notes", "owner_id", _visitor([])) is None


@pytest.mark.parametrize("app,wording", [("writes-01-visitor-insert", "can add rows"),
                                         ("writes-02-spoofed-owner", "names someone else")])
def test_review_finds_exactly_the_planted_flaw_and_the_fixed_twin_is_clean(app, wording, tmp_path):
    out = tmp_path / "report.md"
    assert main(["review", str(PLANTED / app / "vulnerable" / "migrations"), "--out", str(out)]) == 1
    report = out.read_text(encoding="utf-8")
    assert report.count("\n## ") == 1 and wording in report and "removed it again" in report
    assert main(["review", str(PLANTED / app / "fixed" / "migrations"), "--out", str(out)]) == 0
