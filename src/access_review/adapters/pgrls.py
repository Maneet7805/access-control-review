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
    mapped = Mapped("pgrls")
    try:
        data = json.loads(text)
        for violation in data["violations"]:
            parts = violation["location"].split(".")
            flaw = _flaw(violation)
            if flaw and len(parts) > 1 and clean(parts[1]):
                mapped.add(violation["rule_id"], flaw, json.dumps(violation, sort_keys=True), table=clean(parts[1]))
            else:
                mapped.skip()
        skipped = data.get("skipped_rules") or []
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        return unreadable(app, side, f"pgrls: output not readable ({error.__class__.__name__}: {error})")
    return mapped.run(app, side, [f"pgrls: {len(skipped)} rule(s) skipped, so an empty result is not a pass"])
