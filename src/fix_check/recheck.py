"""The four conditions of a fix check (docs/EVALUATION.md section 6) for one app and one fix file.

Nothing is written into the app folder: the attempt is built in a temporary folder.
"""
import json
import tempfile
from pathlib import Path

from access_review.cli import review
from access_review.sandbox import NotCheckable, sandbox
from access_review.scoring import _matches, _target, load_key
from fix_check.allowed import check_allowed
from fix_check.attempt import AttemptRefused, build_attempt

NAMES = {1: "the app still builds with the fix", 2: "the same attack now fails",
         3: "what must keep working still works", 4: "no new leak"}
NOT_RUN = "not run"
PROBE_NOTE = "These tests could not run"


class CannotRun(Exception):
    """The check itself cannot be made (exit code 2). The message is a plain reason."""


def _proved(findings):
    return [f.to_dict() for f in findings if f.status == "proved"]


def _identity(finding):
    return (finding["flaw_id"], *_target(finding))


def _name(finding):
    return f'{finding["flaw_id"]} on {finding.get("table") or finding.get("function")}'


def _result(passed, detail):
    return {"result": "pass" if passed else "fail", "detail": detail}


def _guard(notes, what):
    """A review with tests that could not run cannot be judged either way, so the check cannot run."""
    if any(n.startswith(PROBE_NOTE) for n in notes):
        raise CannotRun(f"some tests could not run on {what}, so it cannot be judged: " + " ".join(notes))


def _vulnerable_identities(vulnerable):
    try:
        with sandbox(vulnerable, baseline=True) as box:
            findings, notes = review(box)
    except NotCheckable as error:
        raise CannotRun(f"the vulnerable app cannot be rebuilt: {error}") from error
    _guard(notes, "the vulnerable app")
    return {_identity(f) for f in _proved(findings)}


def recheck(app, fix_sql, key=None):
    """Run the four conditions. Returns the run object. Raises CannotRun when the check cannot be made."""
    app = Path(app).resolve()
    key = key if key is not None else load_key(app.parent / "answer_key.json")
    vulnerable = app / "vulnerable" / "migrations"
    if app.name not in key or not vulnerable.is_dir():
        raise CannotRun(f"{app.name} has no vulnerable/migrations folder or no entry in the answer key")
    entry, notes = key[app.name], []
    conditions = {n: {"result": NOT_RUN, "detail": ""} for n in NAMES}
    with tempfile.TemporaryDirectory() as tmp:
        try:
            attempt = build_attempt(vulnerable, fix_sql, Path(tmp) / "attempt")
        except AttemptRefused as error:
            raise CannotRun(f"the fix was refused: {error}") from error
        try:
            with sandbox(attempt, baseline=True) as box:
                findings, review_notes = review(box)
                allowed = check_allowed(box, app.name, key)
        except NotCheckable as error:
            conditions[1] = _result(False, f"the app cannot be rebuilt with the fix: {error}")
        else:
            conditions[1] = _result(True, "the app builds with the fix")
            _guard(review_notes, "the fixed copy")
            notes += review_notes
            proved = _proved(findings)
            still = [f for f in proved if any(_matches(flaw, f) for flaw in entry["flaws_vulnerable"])]
            conditions[2] = _result(not still, "still proved: " + ", ".join(map(_name, still)) if still
                                    else "no planted flaw is proved any more")
            counted = [item for item in allowed if not item["expected_failure"]]
            broken = [item for item in counted if not item["holds"]]
            detail = f"{len(counted) - len(broken)} of {len(counted)} allowed entries hold" + "".join(
                f'; broken: {i["entry"]["action"]} {i["entry"].get("table") or i["entry"].get("function")}'
                f' ({i["reason"]})' for i in broken)
            if not entry["allowed"]:
                detail = "the allowed list is empty, so this passes with nothing to check"
                notes.append("The allowed list of this app is empty, so condition 3 passes with nothing to check.")
            conditions[3] = _result(not broken, detail)
            known = _vulnerable_identities(vulnerable)
            new = [f for f in proved if _identity(f) not in known]
            conditions[4] = _result(not new, "new: " + ", ".join(map(_name, new)) if new else "no new proved finding")
    return {"app": app.name, "conditions": {str(n): c for n, c in conditions.items()},
            "broken": [n for n, c in conditions.items() if c["result"] == "fail"], "notes": notes,
            "works": all(c["result"] == "pass" for c in conditions.values())}


def format_run(run):
    lines = [f'Condition {n} ({NAMES[int(n)]}): {c["result"].upper()}' + (f' - {c["detail"]}' if c["detail"] else "")
             for n, c in run["conditions"].items()]
    lines.append("fix works" if run["works"] else "fix does not work")
    return "\n".join(lines) + "\n" + json.dumps(run, indent=2, sort_keys=True)
