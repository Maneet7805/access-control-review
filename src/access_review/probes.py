"""Attacks run against a rebuilt database. Execution decides the result."""
import psycopg


def visitor_reads_rows(connection_string, table):
    """Rows an unauthenticated visitor (role anon) can read from `table`."""
    with psycopg.connect(connection_string, autocommit=True) as conn:
        conn.execute("SET ROLE anon")
        return conn.execute(f'SELECT * FROM "{table}"').fetchall()
