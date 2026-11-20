"""Condition 3 of the fix check: do the entries of an app's `allowed` list still hold on a rebuilt app?

Read, write and call entries each have a rule. Any other entry is returned as not checkable, never skipped.
Every write and call runs in a transaction that is rolled back, so the database is unchanged afterwards.
"""
import json
import subprocess

from psycopg import sql

from access_review.cli import FUNCTIONS_QUERY, TABLES_QUERY
from access_review.evidence import Evidence
from access_review.identity import _act_as, as_user, as_visitor
from access_review.probes import (
    COLUMNS_QUERY,
    PRIVATE_WORDS,
    REFUSALS,
    TEST_VALUES,
    _call_function,
    _failed,
    user_calls_function,
    user_deletes_rows,
    user_inserts_row_for_other,
    user_reads_rows,
    user_reads_view,
    user_updates_rows,
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
WRITE_RULES = {("update", "own_row_changed"), ("insert", "own_owner_accepted"), ("delete", "own_row_deleted")}
CALL_RULES = {("call", "call_runs"), ("call", "own_note_changed"), ("call", "own_rows_only")}


def _check_write(box, entry):
    expect, table, user_id = entry["expect"], entry["table"], USERS.get(entry["actor"])
    owner = owner_column(box, table) if user_id else None
    if user_id is None or owner is None:
        return _not_checkable(entry)
    if expect == "own_owner_accepted":
        evidence = user_inserts_row_for_other(box, table, owner, user_id, user_id)
    elif expect == "own_row_changed":
        evidence = user_updates_rows(box, table, owner, user_id)
    else:
        evidence = user_deletes_rows(box, table, user_id)
    if evidence.result != "ok":
        return _verdict(entry, evidence, False, "action_refused")
    if expect == "own_owner_accepted":
        holds = bool(evidence.rows_seen)
        return _verdict(entry, evidence, holds, None if holds else "no_row_written")
    # The probes touch every row the database lets the actor touch. The entry holds when one of them is the actor's own.
    holds = any(str(row.get(owner)) == user_id for row in evidence.rows_seen)
    return _verdict(entry, evidence, holds, None if holds else "own_row_untouched")


def _own_row(box, user_id):
    """(table, id, count of the user's rows) for the first public table with an owner column and a uuid id column."""
    for table in json.loads(box.run(TABLES_QUERY)):
        owner = owner_column(box, table)
        columns = json.loads(box.run(sql.SQL(COLUMNS_QUERY).format(sql.Literal(table)).as_string()))
        if owner and any(c["name"] == "id" and c["type"] == "uuid" for c in columns):
            query = sql.SQL("SELECT coalesce(json_agg(id), '[]') FROM {} WHERE {} = {}").format(
                sql.Identifier("public", table), sql.Identifier(owner), sql.Literal(user_id))
            ids = json.loads(box.run(query.as_string()))
            if ids:
                return table, ids[0], len(ids)
    return None


def _own_note_changed(box, entry, function, user_id, table, row_id):
    """Call the function as the user with the id of the user's own row. It holds when that row changed."""
    if function["args"][:1] != ["uuid"] or any(kind not in TEST_VALUES for kind in function["args"]):
        return _not_checkable(entry)
    arguments = [sql.Literal(row_id).as_string() + "::uuid"] + [f"{TEST_VALUES[k]}::{k}" for k in function["args"][1:]]
    row = sql.SQL("SELECT to_jsonb(t) FROM {} t WHERE id = {}").format(
        sql.Identifier("public", table), sql.Literal(row_id)).as_string()
    call = sql.SQL("SELECT {}({})").format(sql.Identifier("public", function["name"]),
                                           sql.SQL(", ").join(map(sql.SQL, arguments))).as_string()
    probe, actor = "user_calls_function", f"user:{user_id}"
    script = (f"BEGIN; SET LOCAL statement_timeout = '10s'; {row}; {as_user(user_id)}{call}; "
              f"RESET ROLE; {row}; ROLLBACK;")
    try:
        lines = box.run(script).splitlines()
    except subprocess.CalledProcessError as error:
        return _verdict(entry, _failed(probe, actor, call, error), False, "action_refused")
    before, after = json.loads(lines[0]), json.loads(lines[-1])
    changed = before != after
    return _verdict(entry, Evidence(probe, actor, call, "ok", [after] if changed else []), changed,
                    None if changed else "own_row_untouched")


def _check_call(box, entry):
    expect, actor = entry["expect"], entry["actor"]
    user_id = USERS.get(actor)
    if actor != "service-role" and user_id is None:
        return _not_checkable(entry)
    function = next((f for f in json.loads(box.run(FUNCTIONS_QUERY)) if f["name"] == entry["function"]), None)
    if function is None:
        return _not_checkable(entry)
    if expect == "call_runs":
        identity = _act_as("service_role", {"role": "service_role"}) if actor == "service-role" else as_user(user_id)
        evidence = _call_function(box, "service_role_calls_function", actor, identity, function)
        return _verdict(entry, evidence, evidence.result == "ok", None if evidence.result == "ok" else "action_refused")
    own = _own_row(box, user_id) if user_id else None
    if own is None:
        return _not_checkable(entry)
    if expect == "own_note_changed":
        return _own_note_changed(box, entry, function, user_id, *own[:2])
    evidence = user_calls_function(box, function, user_id)
    values = [next(iter(row.values()), None) for row in evidence.rows_seen]
    holds = evidence.result == "ok" and values == [own[2]]
    return _verdict(entry, evidence, holds, None if holds else
                    "action_refused" if evidence.result != "ok" else "own_rows_missing")


def _check_entry(box, entry):
    rule = (entry.get("action"), entry.get("expect"))
    if rule in READ_RULES:
        return _check_read(box, entry)
    if rule in WRITE_RULES:
        return _check_write(box, entry)
    return _check_call(box, entry) if rule in CALL_RULES else _not_checkable(entry)


def check_allowed(box, app, key):
    """One item per entry of key[app]["allowed"]: {entry, holds, reason, evidence, expected_failure}.

    An entry with `expected_failure` is returned with that field set. The caller leaves those out when it decides
    condition 3. An entry with no rule (an unknown action or expect) is `holds: false` with reason `not_checkable`.
    """
    return [_check_entry(box, entry) for entry in key[app]["allowed"]]
