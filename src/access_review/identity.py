"""Act as a visitor or a signed-in user on a database connection.

Sets the Postgres role and the JWT claims that a Supabase app reads through auth.uid(), auth.role() and auth.jwt().
"""
import json

from psycopg import sql


def _act_as(conn, role, claims):
    conn.execute("RESET ROLE")
    # Clear the old per-claim settings too, so nothing from an earlier identity can leak into this one.
    conn.execute(
        "SELECT set_config('request.jwt.claims', %s, false), "
        "set_config('request.jwt.claim.sub', '', false), set_config('request.jwt.claim.role', '', false)",
        [json.dumps(claims) if claims else ""],
    )
    conn.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(role)))


def as_visitor(conn):
    """Become an unauthenticated visitor: role anon, no claims, so auth.uid() is null."""
    _act_as(conn, "anon", None)


def as_user(conn, user_id):
    """Become a signed-in user: role authenticated, claims with sub=user_id, so auth.uid() returns it."""
    _act_as(conn, "authenticated", {"sub": str(user_id), "role": "authenticated"})
