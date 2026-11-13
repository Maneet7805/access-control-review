from dataclasses import replace

import pytest
from conftest import ROOT

from access_review.evidence import Evidence
from access_review.findings import Finding
from access_review.report import GLOSSARY, NO_VIOLATION, render_report

GOLDEN = ROOT / "tests" / "golden"
USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"
PROFILES = [
    {"id": "aaaaaaaa-0000-0000-0000-000000000001", "owner_id": USER_A, "email": "a@example.test", "bio": "bio of A"},
    {"id": "aaaaaaaa-0000-0000-0000-000000000002", "owner_id": USER_B, "email": "b@example.test", "bio": "bio of B"},
]
POSTS = [{"id": "bbbbbbbb-0000-0000-0000-000000000001", "title": "Hello", "body": "First post"}]


def _user_finding():
    evidence = Evidence("user_reads_rows", f"user:{USER_A}", 'SELECT * FROM "public"."profiles"', "ok", PROFILES)
    return Finding(
        id=f"R2:profiles:user:{USER_A}", flaw_id="R2", actor=f"user:{USER_A}", proof=[evidence], table="profiles",
        explanation='A signed-in user can read rows that belong to other users in the table "profiles".',
        fix='Add a row security policy on "profiles" so a user can only read rows where "owner_id" equals '
            "their own user id (auth.uid()).",
        status="proved")


def _decoy_finding():
    evidence = Evidence("visitor_reads_rows", "visitor", 'SELECT * FROM "public"."posts"', "ok", POSTS)
    return Finding(
        id="R1:posts:visitor", flaw_id="R1", actor="visitor", proof=[evidence], table="posts",
        explanation='A visitor who is not signed in can read the table "posts", which has no owner column. '
                    "It may be public on purpose, so the tool cannot tell.",
        fix='If "posts" should not be public, turn on row security for it and allow reads only for the people '
            "who need them. If it is public on purpose, no change is needed.",
        status="needs_decision")


def _insert_finding(flaw_id):
    visitor = flaw_id == "R3"
    actor = "visitor" if visitor else f"user:{USER_A}"
    probe = "visitor_inserts_row" if visitor else "user_inserts_row_for_other"
    row = {"id": "cccccccc-0000-0000-0000-000000000001", "owner_id": USER_A if visitor else USER_B, "body": "x"}
    statement = 'INSERT INTO "public"."notes" ("owner_id", "body") VALUES (\'x\', \'access-review\')'
    evidence = Evidence(probe, actor, statement, "ok", [row])
    return Finding(
        id=f"{flaw_id}:notes:{actor}", flaw_id=flaw_id, actor=actor, proof=[evidence], table="notes",
        explanation='A visitor who is not signed in can add rows to the table "notes".' if visitor else
                    'A signed-in user can add a row to the table "notes" that names someone else as its owner.',
        fix='Add a row security policy on "notes" so only the right people can add rows.', status="proved")


def _change_finding(flaw_id):
    update = flaw_id == "R5"
    verb = "change" if update else "delete"
    probe = "user_updates_rows" if update else "user_deletes_rows"
    statement = 'UPDATE "public"."notes" SET "body" = \'access-review\'' if update else 'DELETE FROM "public"."notes"'
    rows = [{"id": "cccccccc-0000-0000-0000-000000000001", "owner_id": USER_A, "body": "note of A"},
            {"id": "cccccccc-0000-0000-0000-000000000002", "owner_id": USER_B, "body": "note of B"}]
    evidence = Evidence(probe, f"user:{USER_A}", statement, "ok", rows)
    return Finding(
        id=f"{flaw_id}:notes:user:{USER_A}", flaw_id=flaw_id, actor=f"user:{USER_A}", proof=[evidence], table="notes",
        explanation=f'A signed-in user can {verb} rows that belong to other users in the table "notes".',
        fix=f'Add a row security policy on "notes" so a user can only {verb} their own rows.', status="proved")


# What the rule produces for each planted app (see test_rules.py), with fixed rows so the report is repeatable.
CASES = {
    "rows-01-profiles-vulnerable": [_user_finding()],
    "rows-01-profiles-fixed": [],
    "rows-02-profiles-all-authenticated-vulnerable": [_user_finding()],
    "rows-02-profiles-all-authenticated-fixed": [],
    "rows-03-locked-out-fixed": [],
    "decoy-01-public-posts": [_decoy_finding()],
    "writes-01-visitor-insert-vulnerable": [_insert_finding("R3")],
    "writes-02-spoofed-owner-vulnerable": [_insert_finding("R4")],
    "writes-03-update-others-vulnerable": [_change_finding("R5")],
    "writes-04-delete-others-vulnerable": [_change_finding("R6")],
}


@pytest.mark.parametrize("name", CASES)
def test_report_matches_its_golden_file(name):
    assert render_report(name, CASES[name]) == (GOLDEN / f"{name}.md").read_text(encoding="utf-8")


def test_different_findings_give_different_reports():
    # Negative control for the golden files: they are not all the same text.
    assert len({(GOLDEN / f"{name}.md").read_text(encoding="utf-8") for name in CASES}) > 2


def test_no_finding_gives_the_exact_sentence():
    assert NO_VIOLATION == "No violation found under this test."
    assert NO_VIOLATION in render_report("any-app", [])


def test_the_word_secure_never_appears():
    for name in CASES:
        assert "secure" not in render_report(name, CASES[name]).lower()


def test_needs_decision_is_never_called_proved():
    report = render_report("decoy-01-public-posts", CASES["decoy-01-public-posts"])
    assert "Needs your decision" in report and "Proved" not in report


def test_jargon_is_explained_at_first_use_only():
    finding = replace(_user_finding(),
                      fix="Turn on RLS and add a policy for anon. Check the JWT. Then check the RLS policy again.")
    report = render_report("jargon", [finding])
    for term, meaning in GLOSSARY:
        assert report.count(f"({meaning})") == 1, term
        first_use = report.index(term)
        assert report[first_use + len(term):].startswith(f" ({meaning})"), term


def test_data_with_a_backtick_cannot_close_the_code_span():
    evidence = Evidence("visitor_reads_rows", "visitor", 'SELECT * FROM "public"."posts"', "ok",
                        [{"title": "x` **bold** `y"}])
    finding = replace(_decoy_finding(), proof=[evidence])
    report = render_report("tick", [finding])
    row_line = next(line for line in report.splitlines() if "bold" in line)
    assert row_line.count("`") == 2


def test_notes_go_at_the_end_of_the_report():
    report = render_report("notes", [], notes=["Be careful."])
    assert report.rstrip().endswith("**Note:** Be careful.") and NO_VIOLATION in report


def test_a_newline_in_a_name_cannot_start_a_new_line_or_heading():
    evidence = Evidence("visitor_reads_rows", "visitor", 'SELECT * FROM "public"."a\n# Forged"', "ok", [{"id": 1}])
    finding = replace(_decoy_finding(), proof=[evidence], explanation="Table a\n# Forged is readable")
    report = render_report("app\n# Forged", [finding])
    assert not any(line.startswith("# Forged") or line.startswith("## Forged") for line in report.splitlines())
    assert "\x0a" in report


def test_unicode_line_separators_are_escaped_too():
    report = render_report("a\u2028b\x85c", [])
    assert "\u2028" not in report and "\x85" not in report
