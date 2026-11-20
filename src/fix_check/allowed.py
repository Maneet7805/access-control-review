"""Condition 3 of the fix check: do the entries of an app's `allowed` list still hold on a rebuilt app?

This module covers the read entries. Every other entry is returned as not checkable, never skipped.
"""
import json
import subprocess

from psycopg import sql

from access_review.evidence import Evidence
from access_review.identity import as_user, as_visitor
from access_review.probes import (
    COLUMNS_QUERY,
    PRIVATE_WORDS,
    REFUSALS,
    user_reads_rows,
    user_reads_view,
    visitor_reads_rows,
)
from access_review.rules import owner_column

# Every planted app seeds these users. An actor not listed here has no rule.
USERS = {"user-a": "11111111-1111-1111-1111-111111111111", "user-b": "22222222-2222-2222-2222-222222222222"}
# A view has no foreign key to auth.users, so its owner column is assumed to be this one (see ASSUMPTIONS.md).
VIEW_OWNER_COLUMN = "owner_id"


def _public_columns(box, table, actor_sql, actor):
    """Evidence of one SELECT of the non-private columns of `table`, run as `actor_sql` (not a probe)."""
    columns = json.loads(box.run(sql.SQL(COLUMNS_QUERY).format(sql.Literal(table)).as_string()))
    names = [c["name"] for c in columns if not PRIVATE_WORDS & set(c["name"].lower().split("_"))]
    if not names:
        return None
    select = sql.SQL("SELECT {} FROM {}").format(sql.SQL(", ").join(map(sql.Identifier, names)),
                                                 sql.Identifier("public", table))
    wrapped = sql.SQL("SELECT coalesce(json_agg(t), '[]'::json) FROM ({}) t").format(select).as_string()
    probe, query = "public_columns_read", select.as_string()
    try:
        return Evidence(probe, actor, query, "ok", json.loads(box.run(actor_sql + wrapped)))
    except subprocess.CalledProcessError as error:
        lines = (error.stderr or "").strip().splitlines()
        message = lines[0] if lines else "unknown error"
        result = "permission_denied" if any(text in message for text in REFUSALS) else "error"
        return Evidence(probe, actor, query, result, [], message)


def _verdict(entry, evidence, holds, reason=None):
    return {"entry": entry, "holds": holds, "reason": reason, "evidence": evidence,
            "expected_failure": entry.get("expected_failure")}


def _not_checkable(entry):
    return _verdict(entry, None, False, "not_checkable")


def _check_read(box, entry):
    expect, table, actor = entry["expect"], entry.get("table"), entry["actor"]
    user_id = USERS.get(actor)
    if expect in ("own_row_only", "team_rows_visible", "own_row_visible") and user_id is None:
        return _not_checkable(entry)
    if expect == "public_columns_readable":
        if actor != "visitor" and user_id is None:
            return _not_checkable(entry)
        evidence = _public_columns(box, table, as_visitor() if actor == "visitor" else as_user(user_id), actor)
        if evidence is None:
            return _not_checkable(entry)
        return _verdict(entry, evidence, evidence.result == "ok" and bool(evidence.rows_seen))
    if expect == "public":
        if actor != "visitor":
            return _not_checkable(entry)
        evidence = visitor_reads_rows(box, table)
    elif expect == "own_row_visible":
        evidence = user_reads_view(box, table, user_id)
    else:
        evidence = user_reads_rows(box, table, user_id)
    if evidence.result != "ok" or not evidence.rows_seen:
        return _verdict(entry, evidence, False, "no_rows_returned")
    if expect in ("own_row_only", "own_row_visible"):
        owner = owner_column(box, table) or (VIEW_OWNER_COLUMN if expect == "own_row_visible" else None)
        if owner is None:
            return _not_checkable(entry)
        owned = [str(row.get(owner)) == user_id for row in evidence.rows_seen]
        holds = all(owned) if expect == "own_row_only" else any(owned)
        return _verdict(entry, evidence, holds, None if holds else "own_row_missing")
    return _verdict(entry, evidence, True)  # public, team_rows_visible: any rows count


READ_RULES = {("read", "own_row_only"), ("read", "public"), ("read", "team_rows_visible"),
              ("read_view", "own_row_visible"), ("read_column", "public_columns_readable")}


def check_allowed(box, app, key):
    """One item per entry of key[app]["allowed"]: {entry, holds, reason, evidence, expected_failure}.

    An entry with `expected_failure` is returned with that field set. The caller leaves those out when it decides
    condition 3. An entry with no rule (write and call entries, or an unknown action or expect) is `holds: false`
    with reason `not_checkable`.
    """
    return [
        _check_read(box, entry) if (entry.get("action"), entry.get("expect")) in READ_RULES else _not_checkable(entry)
        for entry in key[app]["allowed"]
    ]
