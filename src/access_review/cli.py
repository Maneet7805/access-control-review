"""Command line: python -m access_review review <migrations_dir> --out report.md

Exit code 0: nothing proved. 1: at least one problem proved. 2: the app could not be rebuilt.
"""
import argparse
import sys
from pathlib import Path

from access_review.probes import user_reads_rows, visitor_reads_rows
from access_review.report import render_report
from access_review.rules import another_users_rows, owner_column
from access_review.sandbox import NotCheckable, sandbox

# The user probes act as the first 2 users already in auth.users.
TEST_USERS_QUERY = "SELECT id FROM auth.users ORDER BY id LIMIT 2"


def review(box):
    """Probe every table in public as a visitor and as each test user. One finding per flaw and table."""
    tables = box.run("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1").splitlines()
    users = box.run(TEST_USERS_QUERY).splitlines()
    findings, seen = [], set()
    for table in tables:
        owner = owner_column(box, table)
        evidence = [visitor_reads_rows(box, table)] + [user_reads_rows(box, table, user) for user in users]
        for item in evidence:
            finding = another_users_rows(table, owner, item)
            if finding and (finding.flaw_id, table) not in seen:
                seen.add((finding.flaw_id, table))
                findings.append(finding)
    return findings


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
            findings = review(box)
    except NotCheckable as error:
        print(f"Not checkable: {error}", file=sys.stderr)
        return 2
    Path(args.out).write_text(render_report(args.name or _app_name(args.migrations_dir), findings), encoding="utf-8")
    proved = sum(finding.status == "proved" for finding in findings)
    print(f"{proved} proved, {len(findings) - proved} need a decision. Report: {args.out}")
    return 1 if proved else 0
