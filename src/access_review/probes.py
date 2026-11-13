"""Attacks run against a rebuilt database. Execution decides the result."""
import json
import subprocess

from psycopg import sql

from access_review.evidence import Evidence
from access_review.identity import as_user, as_visitor


def _read_table(box, probe, actor, identity, table):
    select = sql.SQL("SELECT * FROM {}").format(sql.Identifier("public", table))
    query = select.as_string()
    wrapped = sql.SQL("SELECT coalesce(json_agg(t), '[]'::json) FROM ({}) t").format(select).as_string()
    try:
        rows = json.loads(box.run(identity + wrapped))
    except subprocess.CalledProcessError as error:
        lines = (error.stderr or "").strip().splitlines()
        message = lines[0] if lines else "unknown error"
        result = "permission_denied" if "permission denied" in message else "error"
        return Evidence(probe, actor, query, result, [], message)
    return Evidence(probe, actor, query, "ok", rows)


def visitor_reads_rows(box, table):
    """Evidence of the rows an unauthenticated visitor (role anon) can read from `table` in the sandbox `box`."""
    return _read_table(box, "visitor_reads_rows", "visitor", as_visitor(), table)


def user_reads_rows(box, table, user_id):
    """Evidence of the rows a signed-in user (role authenticated, identity `user_id`) can read from `table`."""
    return _read_table(box, "user_reads_rows", f"user:{user_id}", as_user(user_id), table)
