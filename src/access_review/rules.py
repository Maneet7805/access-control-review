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
    if not evidence.probe.endswith("_reads_rows") or evidence.result != "ok" or not evidence.rows_seen:
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


def insert_accepted(table, owner, evidence: Evidence):
    """Finding when `evidence` shows an insert the database should have refused, else None.

    - A visitor adds a row to a table with an owner column: proved (R3).
    - A visitor adds a row to a table with no owner column: needs_decision (R3). It may be a public form.
    - A signed-in user adds a row that names someone else as its owner: proved (R4).
    """
    if evidence.result != "ok" or not evidence.rows_seen:
        return None
    if evidence.probe == "visitor_inserts_row":
        return Finding(
            id=f"R3:{table}:visitor", flaw_id="R3", actor="visitor", proof=[evidence], table=table,
            explanation=f'A visitor who is not signed in can add rows to the table "{table}".',
            fix=f'Add a row security policy on "{table}" so only signed-in users can add rows, and only rows '
                f'where "{owner}" equals their own user id (auth.uid()).' if owner else
                f'If "{table}" should not accept rows from visitors, turn on row security for it and allow '
                "inserts only for signed-in users. If it is a public form on purpose, no change is needed.",
            status="proved" if owner else "needs_decision")
    if evidence.probe == "user_inserts_row_for_other" and owner:
        own_id = evidence.actor.removeprefix("user:")
        if any(str(row.get(owner)) != own_id for row in evidence.rows_seen):
            return Finding(
                id=f"R4:{table}:{evidence.actor}", flaw_id="R4", actor=evidence.actor, proof=[evidence],
                table=table,
                explanation=f'A signed-in user can add a row to the table "{table}" that names someone else '
                            "as its owner.",
                fix=f'Add a check to the insert policy on "{table}" so a new row is only accepted when '
                    f'"{owner}" equals their own user id (auth.uid()).',
                status="proved")
    return None


CHANGES = {
    "user_updates_rows": ("R5", "change", "update"),
    "user_deletes_rows": ("R6", "delete", "delete"),
}


def others_rows_changed(table, owner, evidence: Evidence):
    """Finding when a signed-in user changed or deleted rows that belong to someone else, else None.

    The probe touches every row it is allowed to, so rows_seen holds exactly the rows row security let through.
    Proved when any of them is owned by another user (R5 for update, R6 for delete).
    """
    if evidence.probe not in CHANGES or evidence.result != "ok" or not owner:
        return None
    flaw_id, verb, policy = CHANGES[evidence.probe]
    own_id = evidence.actor.removeprefix("user:")
    if not any(str(row.get(owner)) != own_id for row in evidence.rows_seen):
        return None
    return Finding(
        id=f"{flaw_id}:{table}:{evidence.actor}", flaw_id=flaw_id, actor=evidence.actor, proof=[evidence],
        table=table,
        explanation=f'A signed-in user can {verb} rows that belong to other users in the table "{table}".',
        fix=f'Add a row security policy on "{table}" so a user can only {verb} rows where "{owner}" equals their '
            f"own user id (auth.uid()). Check the {policy} policy for a condition that is always true.",
        status="proved")


def owner_changed(table, owner, evidence: Evidence):
    """Finding when a signed-in user handed a row to another user by changing its owner column, else None (R7).

    The probe sets the owner to the other test user on every row it is allowed to touch. A row whose owner is now
    someone other than the actor means the update policy has no working check on the new values.
    """
    if evidence.probe != "user_changes_row_owner" or evidence.result != "ok" or not owner:
        return None
    own_id = evidence.actor.removeprefix("user:")
    if not any(str(row.get(owner)) != own_id for row in evidence.rows_seen):
        return None
    return Finding(
        id=f"R7:{table}:{evidence.actor}", flaw_id="R7", actor=evidence.actor, proof=[evidence], table=table,
        explanation=f'A signed-in user can change who owns a row in the table "{table}", handing it to another user.',
        fix=f'Add a check to the update policy on "{table}" so a changed row must still have "{owner}" equal to '
            "the user's own user id (auth.uid()). In SQL this is the WITH CHECK part of the policy.",
        status="proved")
