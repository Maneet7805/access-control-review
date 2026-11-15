import json

import pytest
from conftest import PLANTED

from access_review.cli import FUNCTIONS_QUERY, main
from access_review.evidence import Evidence
from access_review.probes import user_calls_function, visitor_calls_function
from access_review.rules import function_callable
from access_review.sandbox import sandbox

ANSWER_KEY = json.loads((PLANTED / "answer_key.json").read_text())
APPS = [app for app in ANSWER_KEY if app.startswith("functions-")]
VARIANTS = [(app, variant) for app in APPS for variant in ("vulnerable", "fixed")]
USER_A = "11111111-1111-1111-1111-111111111111"
NOTE_A = "cccccccc-0000-0000-0000-000000000001"
AS_USER_A = f"SET ROLE authenticated; SET request.jwt.claims = '{{\"sub\": \"{USER_A}\"}}'; "


def _migrations(app, variant):
    return PLANTED / app / variant / "migrations"


def _function(box):
    (function,) = json.loads(box.run(FUNCTIONS_QUERY))
    return function


def _calls(box):
    function = _function(box)
    return function, visitor_calls_function(box, function), user_calls_function(box, function, USER_A)


@pytest.mark.parametrize("app,variant", VARIANTS)
def test_function_probes_match_answer_key(app, variant):
    with sandbox(_migrations(app, variant), baseline=True) as box:
        function, visitor, user = _calls(box)
    planted = {f["flaw_id"] for f in ANSWER_KEY[app][f"flaws_{variant}"]}
    found = {finding.flaw_id for finding in (function_callable(function, visitor), function_callable(function, user))
             if finding and finding.status == "proved"}
    # A visitor who can call it makes the user finding redundant (the CLI keeps one per function), so U1 and U2 are
    # compared only when the visitor is refused.
    assert (visitor.result == "ok") == ("U3" in planted) == ("U3" in found)
    if "U3" not in planted:
        assert found & {"U1", "U2"} == planted & {"U1", "U2"}


@pytest.mark.parametrize("app", APPS)
def test_the_test_calls_are_rolled_back(app):
    with sandbox(_migrations(app, "vulnerable"), baseline=True) as box:
        _calls(box)
        assert box.run("select count(*) from auth.users") == "2"
        if app.startswith("functions-02"):
            assert box.run("select string_agg(body, ',' order by body) from public.notes") == "note of A,note of B"


def test_a_refused_call_is_permission_denied_not_an_error():
    with sandbox(_migrations("functions-01-admin-delete-any-user", "fixed"), baseline=True) as box:
        function, visitor, user = _calls(box)
    assert (user.result, user.rows_seen) == ("permission_denied", []) and "permission denied" in user.error
    assert visitor.result == "permission_denied"
    assert function_callable(function, user) is None


def test_a_function_that_refuses_on_purpose_is_permission_denied_not_an_error():
    # Negative control for U1: the fixed twin raises an error for a caller who does not own the note.
    with sandbox(_migrations("functions-02-security-definer-no-check", "fixed"), baseline=True) as box:
        function, _, user = _calls(box)
    assert user.result == "permission_denied" and "not your note" in user.error
    assert function_callable(function, user) is None


def test_the_service_role_can_still_call_the_admin_function_in_the_fixed_twin():
    with sandbox(_migrations("functions-01-admin-delete-any-user", "fixed"), baseline=True) as box:
        # A refusal would raise an error here, so reaching the assert means the call ran.
        box.run("BEGIN; SET ROLE service_role; select public.admin_delete_user(gen_random_uuid()); ROLLBACK;")
        assert box.run("select count(*) from auth.users") == "2"


def test_the_owner_can_still_use_the_functions_in_the_fixed_twins():
    with sandbox(_migrations("functions-02-security-definer-no-check", "fixed"), baseline=True) as box:
        box.run(f"BEGIN; {AS_USER_A}select public.set_note_body('{NOTE_A}', 'x'); ROLLBACK;")
    with sandbox(_migrations("functions-03-default-execute", "fixed"), baseline=True) as box:
        _, _, user = _calls(box)
    assert user.result == "ok" and user.rows_seen == [{"result": 1}]  # row security: only their own note


def test_a_function_with_an_argument_type_we_cannot_fill_is_an_error_not_a_finding(tmp_path):
    (tmp_path / "001.sql").write_text(
        "create function public.where_is(spot point) returns text language sql as $$ select 'x' $$;")
    with sandbox(tmp_path, baseline=True) as box:
        function = _function(box)
        evidence = visitor_calls_function(box, function)
    assert evidence.result == "error" and "point" in evidence.error
    assert function_callable(function, evidence) is None


def test_trigger_functions_are_not_listed(tmp_path):
    (tmp_path / "001.sql").write_text(
        "create table public.t (id int);"
        "create function public.on_t() returns trigger language plpgsql as $$ begin return new; end $$;"
        "create trigger t_trigger before insert on public.t for each row execute function public.on_t();")
    with sandbox(tmp_path, baseline=True) as box:
        assert json.loads(box.run(FUNCTIONS_QUERY)) == []


def _evidence(probe, result="ok", rows=None):
    actor = "visitor" if probe.startswith("visitor") else f"user:{USER_A}"
    return Evidence(probe, actor, "SELECT", result, [{"result": 1}] if rows is None else rows)


DEFINER = {"name": "do_thing", "definer": True, "args": []}
INVOKER = {"name": "do_thing", "definer": False, "args": []}
ADMIN = {"name": "admin_delete_user", "definer": True, "args": []}


def test_rule_flaw_ids_follow_who_called_and_what_the_function_is():
    cases = ((DEFINER, "visitor_calls_function", "U3"), (ADMIN, "user_calls_function", "U2"),
             (DEFINER, "user_calls_function", "U1"))
    for function, probe, flaw_id in cases:
        finding = function_callable(function, _evidence(probe))
        assert (finding.flaw_id, finding.status, finding.function) == (flaw_id, "proved", function["name"])


def test_a_visitor_calling_a_function_with_the_callers_rights_needs_a_decision():
    assert function_callable(INVOKER, _evidence("visitor_calls_function")).status == "needs_decision"


def test_a_signed_in_user_calling_an_ordinary_function_with_the_callers_rights_is_no_finding():
    assert function_callable(INVOKER, _evidence("user_calls_function")) is None


def test_a_call_that_did_not_run_gives_no_finding():
    for result in ("permission_denied", "error"):
        assert function_callable(DEFINER, _evidence("user_calls_function", result, [])) is None
    assert function_callable(DEFINER, _evidence("user_reads_rows")) is None


@pytest.mark.parametrize("app,wording", [("functions-01-admin-delete-any-user", "not an admin can call"),
                                         ("functions-02-security-definer-no-check", "A signed-in user can call"),
                                         ("functions-03-default-execute", "visitor who is not signed in can call")])
def test_review_finds_exactly_the_planted_flaw_and_the_fixed_twin_is_clean(app, wording, tmp_path):
    out = tmp_path / "report.md"
    assert main(["review", str(_migrations(app, "vulnerable")), "--out", str(out)]) == 1
    report = out.read_text(encoding="utf-8")
    assert report.count("\n## ") == 1 and wording in report and "We undid everything" in report
    assert main(["review", str(_migrations(app, "fixed")), "--out", str(out)]) == 0
    assert "could not run" not in out.read_text(encoding="utf-8")
