"""Attacks run against a rebuilt database. Execution decides the result."""
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from access_review.identity import as_user, as_visitor

CONNECT_TIMEOUT_SECONDS = 10


# TODO(Maneet, 09 Nov 2026): probes accept any connection string; make them take only a sandbox-issued connection.
def visitor_reads_rows(connection_string, table):
    """Rows an unauthenticated visitor (role anon) can read from `table`."""
    with psycopg.connect(connection_string, autocommit=True,
                         connect_timeout=CONNECT_TIMEOUT_SECONDS) as conn:
        as_visitor(conn)
        try:
            return conn.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))).fetchall()
        except psycopg.errors.InsufficientPrivilege:
            return []


def user_reads_rows(connection_string, table, user_id):
    """Rows a signed-in user (role authenticated, identity `user_id`) can read from `table`."""
    with psycopg.connect(connection_string, autocommit=True, row_factory=dict_row,
                         connect_timeout=CONNECT_TIMEOUT_SECONDS) as conn:
        as_user(conn, user_id)
        try:
            return conn.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))).fetchall()
        except psycopg.errors.InsufficientPrivilege:
            return []
