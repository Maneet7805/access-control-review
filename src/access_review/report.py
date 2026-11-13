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
    "proved": "Proved. We ran the attack and saw it work.",
    "needs_decision": "Needs your decision. The data was readable, but that may be on purpose.",
}
MAX_ROWS_SHOWN = 3


def _who(actor):
    if actor == "visitor":
        return "Anyone who visits the app without signing in."
    return f"Any signed-in user (we tested as user {actor.removeprefix('user:')})."


def _actor_name(actor):
    return "a visitor who is not signed in" if actor == "visitor" else f"signed-in user {actor.removeprefix('user:')}"


def _plain(text):
    """Control characters (newlines too) become visible escapes, so data cannot start a new line or block."""
    return re.sub(r"[\x00-\x1f\x7f]", lambda match: f"\\x{ord(match.group()):02x}", text)


def _code(text):
    """Text for a Markdown code span: backticks are replaced so the data cannot close the span."""
    return _plain(text).replace("`", "'")


def _proof(evidence):
    rows = evidence.rows_seen
    lines = [f"- What we ran: `{_code(evidence.statement)}`, as {_actor_name(evidence.actor)}.",
             f"- What came back: {len(rows)} row(s)."]
    if rows:
        lines.append(f"- The first {min(len(rows), MAX_ROWS_SHOWN)} row(s):")
        lines += [f"  - `{_code(json.dumps(row, sort_keys=True))}`" for row in rows[:MAX_ROWS_SHOWN]]
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
    lines += [f"{proved} problem(s) proved, {len(ordered) - proved} need your decision.", ""]
    for number, finding in enumerate(ordered, 1):
        lines += [f"## {number}. {_plain(finding.explanation)}", "",
                  f"**Status:** {STATUS_TEXT[finding.status]}", "",
                  f"**Who can do it:** {_who(finding.actor)}", "", "**Proof:**", ""]
        for evidence in finding.proof:
            lines += _proof(evidence)
        lines += ["", "**Suggested fix** (you can give this text to your own AI assistant; "
                      "this tool never changes your code):", "", f"> {_plain(finding.fix)}", ""]
    return _explain_first_use("\n".join(lines + _notes(notes)))
