"""Rules turn evidence into findings. A rule never runs anything itself; it only reads evidence."""
from psycopg import sql

from access_review.evidence import Evidence
from access_review.findings import Finding


def owner_column(box, table):
    """The column of `table` (in public) that references auth.users, or None if there is none."""
    query = sql.SQL(
        "SELECT a.attname FROM pg_constraint c "
        "JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey) "
        "WHERE c.contype = 'f' AND c.confrelid = 'auth.users'::regclass "
        "AND c.conrelid = (SELECT oid FROM pg_class WHERE relname = {} AND relnamespace = 'public'::regnamespace) "
        "LIMIT 1"
    ).format(sql.Literal(table)).as_string()
    return box.run(query) or None


def another_users_rows(table, owner, evidence: Evidence):
    """Finding when `evidence` shows a read that returned rows it should not have, else None.

    - A signed-in user sees rows owned by someone else, and the table has an owner column: proved (R2).
    - A visitor reads a table with no owner column: needs_decision (R1). It may be public on purpose.
    """
    if evidence.result != "ok" or not evidence.rows_seen:
        return None
    if evidence.actor.startswith("user:") and owner:
        own_id = evidence.actor.removeprefix("user:")
        if any(str(row.get(owner)) != own_id for row in evidence.rows_seen):
            return Finding(
                id=f"R2:{table}:{evidence.actor}", flaw_id="R2", actor=evidence.actor, proof=[evidence],
                explanation=f'A signed-in user can read rows that belong to other users in the table "{table}".',
                fix=f'Add a row security policy on "{table}" so a user can only read rows where '
                    f'"{owner}" equals their own user id (auth.uid()).',
                status="proved", table=table)
    if evidence.actor == "visitor" and not owner:
        return Finding(
            id=f"R1:{table}:visitor", flaw_id="R1", actor="visitor", proof=[evidence],
            explanation=f'A visitor who is not signed in can read the table "{table}", which has no owner column. '
                        "It may be public on purpose, so the tool cannot tell.",
            fix=f'If "{table}" should not be public, turn on row security for it and allow reads only for the '
                "people who need them. If it is public on purpose, no change is needed.",
            status="needs_decision", table=table)
    return None
