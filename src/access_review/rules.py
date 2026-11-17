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
    - A visitor reads rows of a table with an owner column: proved (R1). A visitor owns no rows.
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
    if evidence.actor == "visitor" and owner:
        return Finding(
            id=f"R1:{table}:visitor", flaw_id="R1", actor="visitor", proof=[evidence],
            explanation=f'A visitor who is not signed in can read rows in the table "{table}", '
                        "which belong to signed-in users.",
            fix=f'Add a row security policy on "{table}" so only signed-in users can read it, and only rows '
                f'where "{owner}" equals their own user id (auth.uid()).',
            status="proved", table=table)
    if evidence.actor == "visitor":
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


def protected_column_changed(table, column, owner, evidence: Evidence):
    """Finding when a signed-in user changed a protected column on their own row (C1), else None.

    Only the actor's own rows count: changing someone else's row is R5. Which columns are protected is decided by
    their names (see PROTECTED_WORDS in probes.py), so a hit is proved, not a guess.
    """
    if evidence.probe != "user_writes_protected_column" or evidence.result != "ok" or not owner:
        return None
    own_id = evidence.actor.removeprefix("user:")
    if not any(str(row.get(owner)) == own_id for row in evidence.rows_seen):
        return None
    return Finding(
        id=f"C1:{table}.{column}:{evidence.actor}", flaw_id="C1", actor=evidence.actor, proof=[evidence],
        table=table, column=column,
        explanation=f'A signed-in user can change the protected column "{column}" on their own row in the table '
                    f'"{table}".',
        fix=f'Stop users from updating "{column}" on "{table}": take update permission on that column away from '
            f'the signed-in role (revoke update, then grant update only on the columns users may change), '
            "or move it to a table users cannot write.",
        status="proved")


def private_column_read(table, column, owner, evidence: Evidence):
    """Finding when a visitor or a signed-in user read a value of a private column that is not theirs (C2), else None.

    Which columns are private is decided by their names (see PRIVATE_WORDS in probes.py). A visitor owns nothing, so
    any value counts. A signed-in user's own rows do not count; with no owner column, any value counts. Empty (null)
    values show nothing, so they do not count.
    """
    if not evidence.probe.endswith("_reads_private_column") or evidence.result != "ok":
        return None
    own_id = evidence.actor.removeprefix("user:") if evidence.actor.startswith("user:") and owner else None
    if not any(row.get(column) is not None and (own_id is None or str(row.get(owner)) != own_id)
               for row in evidence.rows_seen):
        return None
    return Finding(
        id=f"C2:{table}.{column}:{evidence.actor}", flaw_id="C2", actor=evidence.actor, proof=[evidence],
        table=table, column=column,
        explanation=f'{"A visitor who is not signed in" if evidence.actor == "visitor" else "A signed-in user"} '
                    f'can read the private column "{column}" of other people in the table "{table}".',
        fix=f'Stop visitors and signed-in users from reading "{column}" on "{table}": take away their read access '
            "to the table, then give read access only on the columns that are public. Or move the private column to a "
            "separate table that has its own row security policy.",
        status="proved")


def _shown_by(row, base_rows):
    """True when some row of the table has the same value in every column the view row shares with it."""
    return any(all(base[key] == value for key, value in row.items() if key in base) for base in base_rows)


def view_shows_hidden_rows(view, base, evidence: Evidence, base_evidence: Evidence):
    """Finding (V1) when a user reads, through `view`, a row of its table `base` that the table hides from that user.

    `base_evidence` is the same user reading `base` directly. Proved when a view row matches no row of that read.
    Limits: only views over exactly one table; columns the view computes are ignored; a view that shares no column
    with the table cannot be compared, so it gives no finding.
    """
    if evidence.probe != "user_reads_view" or evidence.result != "ok":
        return None
    if base_evidence.result not in ("ok", "permission_denied"):
        return None
    base_rows = base_evidence.rows_seen  # a refused table read shows this user no rows
    comparable = [row for row in evidence.rows_seen if not base_rows or set(row) & set(base_rows[0])]
    if not any(not _shown_by(row, base_rows) for row in comparable):
        return None
    return Finding(
        id=f"V1:{view}:{evidence.actor}", flaw_id="V1", actor=evidence.actor, proof=[evidence], table=view,
        explanation=f'The view "{view}" shows a signed-in user rows of the table "{base}" '
                    "that the table itself hides from that user.",
        fix=f'Make the view "{view}" use the rights of the person who reads it, so the row security on "{base}" '
            f'still applies: ALTER VIEW public."{view}" SET (security_invoker = true); (Postgres 15 and above). '
            "On older versions, remove access to the view for anon and authenticated, or move it to a schema "
            "that is not exposed.",
        status="proved")


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
