"""Turn findings into a plain-language report.md. The tool never changes the developer's code."""
import json
import re

NO_VIOLATION = "No violation found under this test."
# Terms that need a plain-words explanation the first time they appear in a report.
GLOSSARY = (
    ("RLS", "row-level security, a database feature that decides which rows each person may see"),
    ("policy", "a rule the database checks before it shows or changes a row"),
    ("anon", "the database role used for visitors who are not signed in"),
    ("JWT", "the signed token that proves who a signed-in user is"),
)
STATUS_TEXT = {
    "proved": "Proved. We carried out the attack on a test copy of your database and it worked.",
    "needs_decision": "Needs your decision. Anyone could read this data. That may be on purpose, so only you can say.",
}
NEEDS_DECISION_FUNCTION = ("Needs your decision. Anyone could run this function. That may be on purpose, "
                           "so only you can say.")
MAX_ROWS_SHOWN = 3


def _who(actor):
    if actor == "visitor":
        return "Anyone who opens your app without signing in."
    return ("Any user who is signed in. We tested with a made-up test account, "
            f"user {actor.removeprefix('user:')}.")


def _actor_name(actor):
    return "a visitor who is not signed in" if actor == "visitor" else f"signed-in user {actor.removeprefix('user:')}"


def _plain(text):
    """Control characters and line separators become visible escapes, so data cannot start a new line."""
    return re.sub(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]", lambda match: f"\\x{ord(match.group()):02x}", text)


def _code(text):
    """Text for a Markdown code span: backticks are replaced so the data cannot close the span."""
    return _plain(text).replace("`", "'")


def _row_text(row):
    return ", ".join(f"{name}: {json.dumps(value)}" for name, value in sorted(row.items()))


def _proof(evidence):
    rows = evidence.rows_seen
    if evidence.probe in ("user_updates_rows", "user_deletes_rows"):
        verb, past = ("change", "changed") if evidence.probe == "user_updates_rows" else ("delete", "deleted")
        shown = rows[:MAX_ROWS_SHOWN]
        return [f"- What we did: acted as {_actor_name(evidence.actor)} and tried to {verb} every row in the table "
                f"with `{_code(evidence.statement)}`. Row security should limit this to the user's own rows.",
                f"- What happened: the database allowed it for {len(rows)} {'row' if len(rows) == 1 else 'rows'}, "
                "including rows that belong to other users. We undid it, so your data is unchanged.",
                f"- The {'row' if len(shown) == 1 else 'rows'} it {past} (name: value):"
                ] + [f"  - `{_code(_row_text(row))}`" for row in shown]
    if evidence.probe.endswith("_calls_function"):
        return [f"- What we did: acted as {_actor_name(evidence.actor)} and called the function "
                f"with `{_code(evidence.statement)}`, using made-up values.",
                "- What happened: the database ran the function. We undid everything it did, so your data is "
                "unchanged.",
                f"- What it returned (name: value): `{_code(_row_text(rows[0]))}`" if rows else
                "- It returned no rows."]
    if evidence.probe == "user_changes_row_owner":
        shown = rows[:MAX_ROWS_SHOWN]
        return [f"- What we did: acted as {_actor_name(evidence.actor)} and tried to give every row in the table "
                f"to another user with `{_code(evidence.statement)}`. Row security should refuse this.",
                f"- What happened: the database allowed it for {len(rows)} {'row' if len(rows) == 1 else 'rows'}. "
                "We undid it, so your data is unchanged.",
                f"- The {'row' if len(shown) == 1 else 'rows'} it changed, with the new owner (name: value):"
                ] + [f"  - `{_code(_row_text(row))}`" for row in shown]
    if "inserts_row" in evidence.probe:
        lines = [f"- What we did: acted as {_actor_name(evidence.actor)} and tried to add a new row "
                 f"with `{_code(evidence.statement)}`.",
                 "- What happened: the database accepted the new row. We removed it again, so your data is unchanged."]
        return lines + ["- The row it accepted (name: value):"] + [f"  - `{_code(_row_text(row))}`" for row in rows]
    lines = [f"- What we did: acted as {_actor_name(evidence.actor)} and asked the database for the table's rows "
             f"with `{_code(evidence.statement)}`.",
             f"- What we got back: {len(rows)} {'row' if len(rows) == 1 else 'rows'} of data."]
    if rows:
        lines.append(f"- {'The row' if len(rows) == 1 else f'The first {min(len(rows), MAX_ROWS_SHOWN)} rows'}"
                     " (each line is one row, shown as name: value):")
        lines += [f"  - `{_code(_row_text(row))}`" for row in rows[:MAX_ROWS_SHOWN]]
    return lines


def _explain_first_use(text):
    for term, meaning in GLOSSARY:
        text = re.sub(rf"\b{term}\b", f"{term} ({meaning})", text, count=1)
    return text


def _notes(notes):
    return ["", *[f"**Note:** {note}" for note in notes]] if notes else []


def render_report(app_name, findings, notes=()):
    """The report for one app as Markdown. `findings` is a list of Finding; `notes` are cautions for the end."""
    lines = [f"# Access review: {_plain(app_name)}", ""]
    if not findings:
        lines += [NO_VIOLATION, "",
                  "This means the attacks this tool tried found nothing. It does not cover every possible attack."]
        return "\n".join(lines + _notes(notes)) + "\n"
    ordered = sorted(findings, key=lambda finding: finding.status != "proved")
    proved = sum(finding.status == "proved" for finding in ordered)
    lines += [f"We attacked a test copy of your app's database. {proved} problem(s) proved, "
              f"{len(ordered) - proved} need your decision.", ""]
    for number, finding in enumerate(ordered, 1):
        status = STATUS_TEXT[finding.status]
        if finding.function and finding.status == "needs_decision":
            status = NEEDS_DECISION_FUNCTION
        lines += [f"## {number}. {_plain(finding.explanation)}", "", f"**Status:** {status}", "",
                  f"**Who can do it:** {_who(finding.actor)}", "", "**What we saw:**", ""]
        for evidence in finding.proof:
            lines += _proof(evidence)
        lines += ["", "**Suggested fix** (you can give this text to your own AI assistant; "
                      "this tool never changes your code):", "", f"> {_plain(finding.fix)}", ""]
    return _explain_first_use("\n".join(lines + _notes(notes)))
