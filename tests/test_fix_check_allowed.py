import json

import pytest
from conftest import PLANTED, ROOT

from access_review.sandbox import sandbox
from fix_check.allowed import check_allowed

ANSWER_KEY = json.loads((PLANTED / "answer_key.json").read_text())
FIXTURES = ROOT / "tests" / "fixtures" / "fixcheck"
READ_ACTIONS = {"read", "read_view", "read_column"}


def _read_entries(app):
    return [e for e in ANSWER_KEY[app]["allowed"] if e["action"] in READ_ACTIONS]


# Where each app's migrations live: a fixed twin if it has one, else the app itself (decoys and clean apps).
def _migrations(app):
    fixed = PLANTED / app / "fixed" / "migrations"
    return fixed if fixed.is_dir() else PLANTED / app / "migrations"


READ_APPS = [app for app in ANSWER_KEY if _read_entries(app) and _migrations(app).is_dir()]


def _key(entries):
    return {"app": {"allowed": entries}}


@pytest.mark.parametrize("app", READ_APPS)
def test_every_read_entry_without_expected_failure_holds(app):
    with sandbox(_migrations(app), baseline=True) as box:
        items = check_allowed(box, app, ANSWER_KEY)
    for item in items:
        if item["entry"]["action"] not in READ_ACTIONS:
            continue
        assert item["holds"] == (item["expected_failure"] is None), item
        assert item["reason"] != "not_checkable"


def test_locked_out_twin_does_not_hold_and_carries_the_label():
    with sandbox(_migrations("rows-03-locked-out"), baseline=True) as box:
        [item] = check_allowed(box, "rows-03-locked-out", ANSWER_KEY)
    assert item["holds"] is False
    assert item["expected_failure"] == "locks_out_owner"
    assert item["evidence"].rows_seen == []


def test_every_read_entry_of_the_key_has_a_rule():
    # Without a rule an entry would come back as not_checkable; the planted apps with a twin or a folder must not.
    seen = {(e["action"], e["expect"]) for app in ANSWER_KEY for e in _read_entries(app)}
    assert seen == {("read", "own_row_only"), ("read", "public"), ("read", "team_rows_visible"),
                    ("read_view", "own_row_visible"), ("read_column", "public_columns_readable")}


def test_policy_that_hides_every_row_makes_a_read_entry_not_hold():
    entry = {"actor": "user-a", "action": "read", "table": "profiles", "expect": "own_row_only"}
    with sandbox(FIXTURES / "hides-every-row" / "migrations", baseline=True) as box:
        [item] = check_allowed(box, "app", _key([entry]))
    assert item["holds"] is False
    assert item["expected_failure"] is None
    assert item["reason"] == "no_rows_returned"


def test_revoked_public_columns_do_not_hold_but_the_fixed_twin_does():
    entry = {"actor": "visitor", "action": "read_column", "table": "directory", "expect": "public_columns_readable"}
    with sandbox(FIXTURES / "columns-revoked" / "migrations", baseline=True) as box:
        [revoked] = check_allowed(box, "app", _key([entry]))
    assert revoked["holds"] is False
    assert revoked["evidence"].result == "permission_denied"
    with sandbox(_migrations("columns-03-phone-exposed"), baseline=True) as box:
        [fixed] = check_allowed(box, "columns-03-phone-exposed", ANSWER_KEY)
    assert fixed["holds"] is True
    assert fixed["evidence"].rows_seen and all("phone" not in row for row in fixed["evidence"].rows_seen)


@pytest.mark.parametrize("entry", [
    {"actor": "user-a", "action": "read", "table": "t", "expect": "something_new"},
    {"actor": "user-z", "action": "read", "table": "t", "expect": "own_row_only"},
    {"actor": "user-a", "action": "insert", "table": "t", "expect": "own_owner_accepted"},
])
def test_entry_with_no_rule_is_not_checkable(entry):
    # No rule means no query, so no database is needed.
    [item] = check_allowed(None, "app", _key([entry]))
    assert item["holds"] is False
    assert item["reason"] == "not_checkable"
    assert item["entry"] == entry
