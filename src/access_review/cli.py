"""Command line: python -m access_review review <migrations_dir> --out report.md

Exit code 0: nothing proved. 1: at least one problem proved. 2: the app could not be rebuilt.
"""
import argparse
import json
import sys
from pathlib import Path

from access_review.probes import (
    user_calls_function,
    user_deletes_rows,
    user_inserts_row_for_other,
    user_reads_rows,
    user_updates_rows,
    visitor_calls_function,
    visitor_inserts_row,
    visitor_reads_rows,
)
from access_review.report import render_report
from access_review.rules import (
    another_users_rows,
    function_callable,
    insert_accepted,
    others_rows_changed,
    owner_column,
)
from access_review.sandbox import NotCheckable, sandbox

# The user probes act as the first 2 users already in auth.users. Lists come back as JSON, never split on newlines.
TABLES_QUERY = ("SELECT coalesce(json_agg(tablename ORDER BY tablename), '[]') "
                "FROM pg_tables WHERE schemaname = 'public'")
TEST_USERS_QUERY = "SELECT coalesce(json_agg(id), '[]') FROM (SELECT id FROM auth.users ORDER BY id LIMIT 2) u"
# Functions written in public (not trigger functions, not part of an extension), with their argument types.
FUNCTIONS_QUERY = (
    "SELECT coalesce(json_agg(json_build_object('name', p.proname, 'definer', p.prosecdef, 'args', "
    "(SELECT coalesce(json_agg(format_type(t, NULL) ORDER BY o), '[]') "
    "FROM unnest(p.proargtypes::oid[]) WITH ORDINALITY a(t, o))) ORDER BY p.proname, p.oid), '[]') "
    "FROM pg_proc p WHERE p.pronamespace = 'public'::regnamespace AND p.prokind = 'f' "
    "AND p.prorettype <> 'trigger'::regtype "
    "AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid = p.oid AND d.deptype = 'e')")
NOTE_NOT_RUN = ("These tests could not run, so this result does not cover them: {}. "
                "Do not read this result as a clean one.")
NOTE_FEW_USERS = ("The app has fewer than 2 users in its database, so the tests that need a signed-in user "
                  "could only partly run. Do not read this result as a clean one.")


def review(box):
    """Probe every table in public as a visitor and as each test user. One finding per flaw and table.

    Returns (findings, notes). Notes are plain-words cautions that go at the end of the report.
    """
    tables = json.loads(box.run(TABLES_QUERY))
    users = json.loads(box.run(TEST_USERS_QUERY))
    findings, seen, not_run = [], set(), set()
    for table in tables:
        owner = owner_column(box, table)
        evidence = [visitor_reads_rows(box, table)] + [user_reads_rows(box, table, user) for user in users]
        if users:
            evidence.append(visitor_inserts_row(box, table, owner, users[0]))
        if owner and len(users) == 2:
            evidence.append(user_inserts_row_for_other(box, table, owner, users[0], users[1]))
        if owner and users:
            evidence += [user_updates_rows(box, table, owner, users[0]), user_deletes_rows(box, table, users[0])]
        for item in evidence:
            if item.result == "error":
                not_run.add(f'{item.probe.replace("_", " ")} on "{table}"')
            finding = (another_users_rows(table, owner, item) or insert_accepted(table, owner, item)
                       or others_rows_changed(table, owner, item))
            if finding and (finding.flaw_id, table) not in seen:
                seen.add((finding.flaw_id, table))
                findings.append(finding)
    for function in json.loads(box.run(FUNCTIONS_QUERY)):
        name = function["name"]
        calls = [visitor_calls_function(box, function)] + [user_calls_function(box, function, u) for u in users[:1]]
        for item in calls:
            if item.result == "error":
                not_run.add(f'{item.probe.replace("_", " ")} "{name}"')
            finding = function_callable(function, item)
            if finding and ("function", name) not in seen:  # one finding per function; the visitor is tried first
                seen.add(("function", name))
                findings.append(finding)
    notes = [NOTE_FEW_USERS] if len(users) < 2 else []
    if not_run:
        notes.append(NOTE_NOT_RUN.format("; ".join(sorted(not_run))))
    return findings, notes


def _app_name(migrations):
    folder = Path(migrations).resolve()
    return folder.parent.name if folder.name == "migrations" else folder.name


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m access_review")
    commands = parser.add_subparsers(dest="command", required=True)
    review_parser = commands.add_parser("review", help="rebuild an app from its migrations and test who can read what")
    review_parser.add_argument("migrations_dir")
    review_parser.add_argument("--out", default="report.md")
    review_parser.add_argument("--name", help="app name for the report title (default: taken from the folder)")
    args = parser.parse_args(argv)
    try:
        with sandbox(args.migrations_dir, baseline=True) as box:
            findings, notes = review(box)
    except NotCheckable as error:
        print(f"Not checkable: {error}", file=sys.stderr)
        return 2
    name = args.name or _app_name(args.migrations_dir)
    Path(args.out).write_text(render_report(name, findings, notes), encoding="utf-8")
    proved = sum(finding.status == "proved" for finding in findings)
    print(f"{proved} proved, {len(findings) - proved} need a decision. Report: {args.out}")
    return 1 if proved else 0
