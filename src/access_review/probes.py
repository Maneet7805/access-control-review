"""Attacks run against a rebuilt database. Execution decides the result."""
import json
import subprocess

from psycopg import sql

from access_review.evidence import Evidence
from access_review.identity import as_user, as_visitor

# What psql says when the database refuses an action. Anything else is reported as a plain error.
# P0001 is the code of an error a function raises on purpose (raise exception); function calls report error codes.
REFUSALS = ("permission denied", "violates row-level security", "P0001")
# A harmless value for each column type, used to fill the columns a test row must have.
TEST_VALUES = {
    "text": "'access-review'", "character varying": "'access-review'",
    "integer": "0", "bigint": "0", "smallint": "0", "numeric": "0", "real": "0", "double precision": "0",
    "boolean": "false", "uuid": "gen_random_uuid()", "date": "current_date",
    "timestamp with time zone": "now()", "timestamp without time zone": "now()",
    "json": "'{}'", "jsonb": "'{}'",
}
COLUMNS_QUERY = (
    "SELECT coalesce(json_agg(json_build_object('name', column_name, 'type', data_type, "
    "'required', is_nullable = 'NO' AND column_default IS NULL AND is_generated = 'NEVER' AND is_identity = 'NO') "
    "ORDER BY ordinal_position), '[]') FROM information_schema.columns "
    "WHERE table_schema = 'public' AND table_name = {}"
)


def _failed(probe, actor, query, error):
    lines = (error.stderr or "").strip().splitlines()
    message = lines[0] if lines else "unknown error"
    result = "permission_denied" if any(text in message for text in REFUSALS) else "error"
    return Evidence(probe, actor, query, result, [], message)


def _read_table(box, probe, actor, identity, table):
    select = sql.SQL("SELECT * FROM {}").format(sql.Identifier("public", table))
    query = select.as_string()
    wrapped = sql.SQL("SELECT coalesce(json_agg(t), '[]'::json) FROM ({}) t").format(select).as_string()
    try:
        rows = json.loads(box.run(identity + wrapped))
    except subprocess.CalledProcessError as error:
        return _failed(probe, actor, query, error)
    return Evidence(probe, actor, query, "ok", rows)


def visitor_reads_rows(box, table):
    """Evidence of the rows an unauthenticated visitor (role anon) can read from `table` in the sandbox `box`."""
    return _read_table(box, "visitor_reads_rows", "visitor", as_visitor(), table)


def user_reads_rows(box, table, user_id):
    """Evidence of the rows a signed-in user (role authenticated, identity `user_id`) can read from `table`."""
    return _read_table(box, "user_reads_rows", f"user:{user_id}", as_user(user_id), table)


def _insert_row(box, probe, actor, identity, table, owner, owner_id):
    """Try to add one row as `identity`, naming `owner_id` as its owner. The write is rolled back.

    Evidence rows_seen holds the row the database accepted, read back inside the same transaction. A refusal,
    or a table whose columns we cannot fill, gives no rows. Nothing is kept: the transaction always ends in ROLLBACK.
    """
    columns = json.loads(box.run(sql.SQL(COLUMNS_QUERY).format(sql.Literal(table)).as_string()))
    names, values = [], []
    for column in columns:
        if column["name"] == owner:
            names.append(sql.Identifier(column["name"]))
            values.append(sql.Literal(str(owner_id)))
        elif column["required"]:
            if column["type"] not in TEST_VALUES:
                message = f'cannot build a test row: column "{column["name"]}" has type {column["type"]}'
                return Evidence(probe, actor, f"INSERT INTO public.{table}", "error", [], message)
            names.append(sql.Identifier(column["name"]))
            values.append(sql.SQL(TEST_VALUES[column["type"]]))
    target = sql.Identifier("public", table)
    insert = (sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(target, sql.SQL(", ").join(names),
                                                                sql.SQL(", ").join(values))
              if names else sql.SQL("INSERT INTO {} DEFAULT VALUES").format(target))
    readback = sql.SQL(
        "SELECT coalesce(jsonb_agg(t), '[]'::jsonb) FROM {} t WHERE t.xmin = pg_current_xact_id()::xid"
    ).format(target)
    query = insert.as_string()
    script = f"BEGIN; {identity}{query}; RESET ROLE; {readback.as_string()}; ROLLBACK;"
    try:
        output = box.run(script)
    except subprocess.CalledProcessError as error:
        return _failed(probe, actor, query, error)
    return Evidence(probe, actor, query, "ok", json.loads(output.splitlines()[-1]))


def visitor_inserts_row(box, table, owner, owner_id):
    """Evidence of whether an unauthenticated visitor can add a row to `table`, naming `owner_id` as its owner."""
    return _insert_row(box, "visitor_inserts_row", "visitor", as_visitor(), table, owner, owner_id)


def user_inserts_row_for_other(box, table, owner, user_id, victim_id):
    """Evidence of whether signed-in `user_id` can add a row to `table` that names `victim_id` as its owner."""
    return _insert_row(box, "user_inserts_row_for_other", f"user:{user_id}", as_user(user_id), table, owner,
                       victim_id)


def _change_run(box, probe, user_id, statement, before_readback, after_readback):
    """Run `statement` as `user_id` inside a transaction that is rolled back. Returns (query, output lines)."""
    query = statement.as_string()
    parts = ["BEGIN;"]
    if before_readback is not None:
        parts.append(f"{before_readback.as_string()};")
    parts += [as_user(user_id), f"{query};", "RESET ROLE;", f"{after_readback.as_string()};", "ROLLBACK;"]
    return query, box.run(" ".join(parts)).splitlines()


def user_updates_rows(box, table, owner, user_id):
    """Evidence of which rows signed-in `user_id` can change in `table`. The change is rolled back.

    The test sets one column to a harmless value on every row, with no WHERE, so row security alone decides which
    rows are touched. rows_seen holds the rows that were changed, read back inside the same transaction.
    """
    actor, probe, target = f"user:{user_id}", "user_updates_rows", sql.Identifier("public", table)
    columns = json.loads(box.run(sql.SQL(COLUMNS_QUERY).format(sql.Literal(table)).as_string()))
    usable = [c for c in columns if c["name"] != owner and c["type"] in TEST_VALUES]
    usable.sort(key=lambda c: c["name"] == "id")  # try the ordinary columns before the id
    readback = sql.SQL(
        "SELECT coalesce(jsonb_agg(t), '[]'::jsonb) FROM {} t WHERE t.xmin = pg_current_xact_id()::xid").format(target)
    failure = Evidence(probe, actor, f"UPDATE public.{table}", "error", [],
                       "cannot build a test change: no column of a type we can set")
    for column in usable:  # a column can fail on a unique or check rule, so try the next one
        update = sql.SQL("UPDATE {} SET {} = {}").format(target, sql.Identifier(column["name"]),
                                                        sql.SQL(TEST_VALUES[column["type"]]))
        try:
            query, lines = _change_run(box, probe, user_id, update, None, readback)
        except subprocess.CalledProcessError as error:
            failure = _failed(probe, actor, update.as_string(), error)
            if failure.result == "permission_denied":
                return failure
            continue
        return Evidence(probe, actor, query, "ok", json.loads(lines[-1]))
    return failure


def user_changes_row_owner(box, table, owner, user_id, new_owner_id):
    """Evidence of whether signed-in `user_id` can hand rows of `table` to `new_owner_id`. The change is rolled back.

    The test sets the owner column to `new_owner_id` on every row, with no WHERE and a literal value, so row security
    alone decides. rows_seen holds the rows whose content changed, compared inside the same transaction. Rows that
    already belonged to `new_owner_id` are left out because nothing about them changed.
    """
    actor, probe, target = f"user:{user_id}", "user_changes_row_owner", sql.Identifier("public", table)
    update = sql.SQL("UPDATE {} SET {} = {}").format(target, sql.Identifier(owner), sql.Literal(str(new_owner_id)))
    before = sql.SQL("SELECT coalesce(jsonb_agg(t), '[]'::jsonb) FROM {} t").format(target)
    after = sql.SQL(
        "SELECT coalesce(jsonb_agg(t), '[]'::jsonb) FROM {} t WHERE t.xmin = pg_current_xact_id()::xid").format(target)
    try:
        query, lines = _change_run(box, probe, user_id, update, before, after)
    except subprocess.CalledProcessError as error:
        return _failed(probe, actor, update.as_string(), error)
    unchanged, changed = json.loads(lines[-2]), []
    for row in json.loads(lines[-1]):  # one by one, so identical rows in a table with no key are counted correctly
        if row in unchanged:
            unchanged.remove(row)
        else:
            changed.append(row)
    return Evidence(probe, actor, query, "ok", changed)


def user_deletes_rows(box, table, user_id):
    """Evidence of which rows signed-in `user_id` can delete from `table`. The delete is rolled back.

    The test deletes every row, with no WHERE, so row security alone decides which rows go. rows_seen holds the rows
    that were gone afterwards, compared inside the same transaction.
    """
    actor, probe, target = f"user:{user_id}", "user_deletes_rows", sql.Identifier("public", table)
    delete = sql.SQL("DELETE FROM {}").format(target)
    everything = sql.SQL("SELECT coalesce(jsonb_agg(t), '[]'::jsonb) FROM {} t").format(target)
    try:
        query, lines = _change_run(box, probe, user_id, delete, everything, everything)
    except subprocess.CalledProcessError as error:
        return _failed(probe, actor, delete.as_string(), error)
    before, after = json.loads(lines[-2]), json.loads(lines[-1])
    remaining, gone = list(after), []
    for row in before:  # one by one, so identical rows in a table with no key are counted correctly
        if row in remaining:
            remaining.remove(row)
        else:
            gone.append(row)
    return Evidence(probe, actor, query, "ok", gone)


def _call_function(box, probe, actor, identity, function):
    """Call `function` (a dict with name and args, as listed by the CLI) once with typed dummy arguments.

    The call runs in a savepoint inside a transaction that is rolled back, with a time limit, so nothing is kept.
    result is ok only when the call actually ran. A refusal (no permission, or an error the function raises on
    purpose) is permission_denied. Anything else, such as an argument type we cannot fill, is an error.
    """
    name, target = function["name"], sql.Identifier("public", function["name"])
    unfillable = [kind for kind in function["args"] if kind not in TEST_VALUES]
    if unfillable:
        message = f'cannot build a test call: an argument has type {unfillable[0]}'
        return Evidence(probe, actor, f"SELECT public.{name}(...)", "error", [], message)
    arguments = sql.SQL(", ").join(sql.SQL(f"{TEST_VALUES[kind]}::{kind}") for kind in function["args"])
    call = sql.SQL("SELECT {}({}) AS result").format(target, arguments)
    wrapped = sql.SQL("SELECT coalesce(jsonb_agg(to_jsonb(f)), '[]'::jsonb) FROM ({}) f").format(call)
    query = call.as_string()
    script = ("\\set VERBOSITY verbose\nBEGIN; SET LOCAL statement_timeout = '10s'; SAVEPOINT call; "
              f"{identity}{wrapped.as_string()}; ROLLBACK TO call; ROLLBACK;")
    try:
        output = box.run(script)
    except subprocess.CalledProcessError as error:
        return _failed(probe, actor, query, error)
    return Evidence(probe, actor, query, "ok", json.loads(output.splitlines()[-1]))


def visitor_calls_function(box, function):
    """Evidence of whether an unauthenticated visitor can call `function`."""
    return _call_function(box, "visitor_calls_function", "visitor", as_visitor(), function)


def user_calls_function(box, function, user_id):
    """Evidence of whether signed-in `user_id` can call `function`."""
    return _call_function(box, "user_calls_function", f"user:{user_id}", as_user(user_id), function)
