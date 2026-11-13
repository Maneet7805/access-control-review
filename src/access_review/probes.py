"""Attacks run against a rebuilt database. Execution decides the result."""
import json
import subprocess

from psycopg import sql

from access_review.identity import as_user, as_visitor


def _rows(box, identity, table):
    query = sql.SQL("SELECT coalesce(json_agg(t), '[]'::json) FROM (SELECT * FROM {}) t").format(
        sql.Identifier(table)).as_string()
    try:
        return json.loads(box.run(identity + query))
    except subprocess.CalledProcessError as error:
        if "permission denied" in (error.stderr or ""):
            return []
        raise


def visitor_reads_rows(box, table):
    """Rows (as dicts) an unauthenticated visitor (role anon) can read from `table` in the sandbox `box`."""
    return _rows(box, as_visitor(), table)


def user_reads_rows(box, table, user_id):
    """Rows (as dicts) a signed-in user (role authenticated, identity `user_id`) can read from `table`."""
    return _rows(box, as_user(user_id), table)
