"""Rules turn evidence into findings. A rule never runs anything itself; it only reads evidence."""
import re

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


ADMIN_NAME = re.compile(r"(^|_)admin(_|$)", re.IGNORECASE)
CALLS = ("visitor_calls_function", "user_calls_function")


def function_callable(function, evidence: Evidence):
    """Finding when `evidence` shows a call the database should have refused, else None.

    `function` is a dict with name and definer (True when it runs with its owner's rights). The call must have run.
    - A visitor can call a function: U3, proved if the function runs with elevated rights, else needs_decision.
    - A signed-in user can call a function with "admin" in its name: U2, same rule.
    - A signed-in user can call any other function that runs with elevated rights: U1, proved.
    A function that runs with the caller's rights is limited by row security, so on its own it is no finding.
    """
    if evidence.probe not in CALLS or evidence.result != "ok":
        return None
    name, elevated = function["name"], function["definer"]
    status = "proved" if elevated else "needs_decision"
    if evidence.probe == "visitor_calls_function":
        flaw_id, who = "U3", "A visitor who is not signed in"
        fix = (f'Run REVOKE EXECUTE ON FUNCTION public."{name}" FROM PUBLIC, anon; (Postgres lets everyone call a new '
               "function unless you remove that). Then allow only the roles that need it. If visitors must call it "
               "on purpose, no change is needed.")
    elif ADMIN_NAME.search(name):
        flaw_id, who = "U2", "A signed-in user who is not an admin"
        fix = (f'Make "{name}" admin-only: run REVOKE EXECUTE ON FUNCTION public."{name}" FROM PUBLIC, anon, '
               "authenticated; and call it only from your server, or check inside the function that the caller is "
               "an admin and raise an error if not.")
    elif elevated:
        flaw_id, who = "U1", "A signed-in user"
        fix = (f'Make "{name}" check who is calling (for example compare auth.uid() with the row owner) and raise an '
               "error if the caller may not do this, or make it run with the caller's rights (security invoker) so "
               "row security applies.")
    else:
        return None
    return Finding(
        id=f"{flaw_id}:{name}:{evidence.actor}", flaw_id=flaw_id, actor=evidence.actor, proof=[evidence],
        function=name, status=status,
        explanation=f'{who} can call the function "{name}", which runs with more rights than the caller.'
                    if elevated else f'{who} can call the function "{name}".',
        fix=fix)
