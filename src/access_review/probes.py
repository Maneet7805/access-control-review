"""Attacks run against a rebuilt database. Execution decides the result."""
import psycopg
from psycopg import sql

CONNECT_TIMEOUT_SECONDS = 10


def visitor_reads_rows(connection_string, table):
    """Rows an unauthenticated visitor (role anon) can read from `table`."""
    with psycopg.connect(connection_string, autocommit=True,
                         connect_timeout=CONNECT_TIMEOUT_SECONDS) as conn:
        conn.execute("SET ROLE anon")
        try:
            return conn.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))).fetchall()
        except psycopg.errors.InsufficientPrivilege:
            return []
