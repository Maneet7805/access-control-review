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
        lines += [f"## {number}. {_plain(finding.explanation)}", "",
                  f"**Status:** {STATUS_TEXT[finding.status]}", "",
                  f"**Who can do it:** {_who(finding.actor)}", "", "**What we saw:**", ""]
        for evidence in finding.proof:
            lines += _proof(evidence)
        lines += ["", "**Suggested fix** (you can give this text to your own AI assistant; "
                      "this tool never changes your code):", "", f"> {_plain(finding.fix)}", ""]
    return _explain_first_use("\n".join(lines + _notes(notes)))
