"""pgrls adapter (JSON from `pgrls lint --format json`). Rules: docs/baselines.md 3.5."""
import json

from access_review.adapters._common import Mapped, clean, unreadable

SIMPLE = {"SEC001": "R1", "SEC038": "R1", "SEC039": "R3", "SEC028": "R4", "SEC020": "R7"}


def _flaw(violation):
    rule, message = violation["rule_id"], violation["message"]
    if rule in SIMPLE:
        return SIMPLE[rule]
    if rule == "SEC049" and "grants SELECT to anon" in message:
        return "R1"
    if rule == "SEC006" and "covers UPDATE" in message:
        return "R7"
    return None


def adapt(text, app, side):
    return adapt_files([(None, text)], app, side)


def adapt_files(outputs, app, side):
    """outputs: (file name, raw text) per migration file, in run order. One run object (docs/baselines.md 2.5).

    With one file the result is the single-file one. With several, each proof line names its file.
    Any unreadable file makes the whole run not_checkable.
    """
    if not outputs:
        return unreadable(app, side, "pgrls: no migration file to read")
    mapped, skipped = Mapped("pgrls"), 0
    for name, text in outputs:
        try:
            data = json.loads(text)
            for violation in data["violations"]:
                parts = violation["location"].split(".")
                flaw = _flaw(violation)
                if flaw and len(parts) > 1 and clean(parts[1]):
                    line = json.dumps(violation, sort_keys=True)
                    mapped.add(violation["rule_id"], flaw, f"{name}: {line}" if len(outputs) > 1 else line,
                               table=clean(parts[1]))
                else:
                    mapped.skip()
            skipped = max(skipped, len(data.get("skipped_rules") or []))
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            where = f" in {name}" if len(outputs) > 1 else ""
            return unreadable(app, side, f"pgrls: output not readable{where} ({error.__class__.__name__}: {error})")
    return mapped.run(app, side, [f"pgrls: {skipped} rule(s) skipped, so an empty result is not a pass"])
