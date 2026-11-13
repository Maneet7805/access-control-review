import json

import pytest
from conftest import PLANTED

from access_review.cli import main
from access_review.evidence import Evidence
from access_review.probes import (
    user_deletes_rows,
    user_inserts_row_for_other,
    user_updates_rows,
    visitor_inserts_row,
)
from access_review.rules import insert_accepted, others_rows_changed
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


READ_APPS = [(app, variant) for app in ("rows-01-profiles", "rows-02-profiles-all-authenticated")
             for variant in ("vulnerable", "fixed")] + [("rows-03-locked-out", "fixed")]


@pytest.mark.parametrize("app,variant", READ_APPS)
def test_the_key_lists_the_write_flaws_the_probes_find_in_the_rows_apps(app, variant):
    with sandbox(PLANTED / app / variant / "migrations", baseline=True) as box:
        visitor = visitor_inserts_row(box, "profiles", "owner_id", USER_A)
        spoof = user_inserts_row_for_other(box, "profiles", "owner_id", USER_A, USER_B)
    assert bool(visitor.rows_seen) == _planted(app, variant, "R3")
    assert bool(spoof.rows_seen) == _planted(app, variant, "R4")


# M3.2: update and delete. Each app is keyed by the flaw it plants and the action the owner must still be able to do.
CHANGE_VARIANTS = [(app, variant) for app in ("writes-03-update-others", "writes-04-delete-others")
                   for variant in ("vulnerable", "fixed")]


def _changes(box):
    return user_updates_rows(box, "notes", "owner_id", USER_A), user_deletes_rows(box, "notes", USER_A)


def _touches_others(evidence):
    return any(row["owner_id"] != USER_A for row in evidence.rows_seen)


@pytest.mark.parametrize("app,variant", CHANGE_VARIANTS)
def test_update_and_delete_probes_match_answer_key(app, variant):
    with sandbox(PLANTED / app / variant / "migrations", baseline=True) as box:
        update, delete = _changes(box)
    assert _touches_others(update) == _planted(app, variant, "R5")
    assert _touches_others(delete) == _planted(app, variant, "R6")


@pytest.mark.parametrize("app,variant", CHANGE_VARIANTS)
def test_update_and_delete_are_rolled_back(app, variant):
    with sandbox(PLANTED / app / variant / "migrations", baseline=True) as box:
        _changes(box)
        assert box.run("select count(*) from public.notes") == "2"
        assert box.run("select string_agg(body, ',' order by body) from public.notes") == "note of A,note of B"


@pytest.mark.parametrize("app,action", [("writes-03-update-others", "update"), ("writes-04-delete-others", "delete")])
def test_the_owner_can_still_change_or_delete_their_own_row_in_the_fixed_twin(app, action):
    # Allowed access: the fix must keep the owner's own row workable. A fix that blocks everything would fail this.
    with sandbox(PLANTED / app / "fixed" / "migrations", baseline=True) as box:
        update, delete = _changes(box)
    evidence = update if action == "update" else delete
    assert [row["owner_id"] for row in evidence.rows_seen] == [USER_A]


def test_a_user_with_no_policy_at_all_changes_nothing():
    # Negative control: writes-01 fixed has insert and select policies only, so update and delete touch no rows.
    with sandbox(PLANTED / "writes-01-visitor-insert" / "fixed" / "migrations", baseline=True) as box:
        update, delete = _changes(box)
    assert update.rows_seen == [] and delete.rows_seen == []


def _change(probe, rows):
    return Evidence(probe, f"user:{USER_A}", "STATEMENT", "ok", rows)


def test_changing_or_deleting_someone_elses_row_is_proved_r5_and_r6():
    rows = [{"owner_id": USER_A}, {"owner_id": USER_B}]
    assert others_rows_changed("notes", "owner_id", _change("user_updates_rows", rows)).flaw_id == "R5"
    assert others_rows_changed("notes", "owner_id", _change("user_deletes_rows", rows)).flaw_id == "R6"


def test_touching_only_their_own_rows_or_nothing_gives_no_finding():
    own = [{"owner_id": USER_A}]
    assert others_rows_changed("notes", "owner_id", _change("user_updates_rows", own)) is None
    assert others_rows_changed("notes", "owner_id", _change("user_deletes_rows", [])) is None
    assert others_rows_changed("notes", None, _change("user_updates_rows", [{"x": 1}])) is None


@pytest.mark.parametrize("app,wording", [("writes-03-update-others", "can change rows"),
                                         ("writes-04-delete-others", "can delete rows")])
def test_review_finds_exactly_the_planted_change_flaw_and_the_fixed_twin_is_clean(app, wording, tmp_path):
    out = tmp_path / "report.md"
    assert main(["review", str(PLANTED / app / "vulnerable" / "migrations"), "--out", str(out)]) == 1
    report = out.read_text(encoding="utf-8")
    assert report.count("\n## ") == 1 and wording in report and "We undid it" in report
    assert main(["review", str(PLANTED / app / "fixed" / "migrations"), "--out", str(out)]) == 0
