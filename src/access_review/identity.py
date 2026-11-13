"""SQL that makes a session act as a visitor or a signed-in user.

Sets the Postgres role and the JWT claims that a Supabase app reads through auth.uid(), auth.role() and auth.jwt().
Put the text in front of a query and run both with Sandbox.run.
"""
import json
import uuid

from psycopg import sql


def _act_as(role, claims):
    claims_text = json.dumps(claims) if claims else ""
    # Clear the old per-claim settings too, so nothing from an earlier identity can leak into this one.
    return sql.SQL(
        "RESET ROLE; SET request.jwt.claims = {}; SET request.jwt.claim.sub = ''; "
        "SET request.jwt.claim.role = ''; SET ROLE {}; "
    ).format(sql.Literal(claims_text), sql.Identifier(role)).as_string()


def as_visitor():
    """Become an unauthenticated visitor: role anon, no claims, so auth.uid() is null."""
    return _act_as("anon", None)


def as_user(user_id):
    """Become a signed-in user: role authenticated, claims with sub=user_id, so auth.uid() returns it."""
    user_id = uuid.UUID(str(user_id))  # rejects anything that is not a UUID
    return _act_as("authenticated", {"sub": str(user_id), "role": "authenticated"})
