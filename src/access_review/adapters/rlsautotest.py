"""rlsautotest adapter (JSON report). Rules: docs/baselines.md 3.4."""
import ast
import json
import re

from access_review.adapters._common import Mapped, clean, unreadable

READ = re.compile(r"^policy .+: SELECT USING \(true\) -> every (\[[^\]]*\]) sees ALL rows")
WRITE = re.compile(r"^policy .+: INSERT WITH CHECK \(true\) -> any (\[[^\]]*\]) may write any row")


def _executed_fired(table):
    """Executed fields that reported something. They have no rule, so each is one unmapped item."""
    grid = (table.get("idgrid") or {}).values()
    count = sum(1 for cmd in grid for cell in cmd.values() if not cell.get("pass", True))
    count += len(table.get("leak_cells") or []) + len(table.get("transition_leaks") or [])
    cells = (table.get("column_security") or {}).get("cells") or {}
    return count + sum(1 for role in cells.values() for cell in role.values() if cell.get("leaked"))


def _footgun(text):
    """R1 or R3 when `anon` is in the role list, R2 or R4 when only signed-in roles are. None if unmapped."""
    for pattern, visitor, signed_in in ((READ, "R1", "R2"), (WRITE, "R3", "R4")):
        match = pattern.match(text)
        if match:
            return visitor if "anon" in ast.literal_eval(match.group(1)) else signed_in
    return None


def _surface(item):
    kind, why = item["type"], item["why"]
    if kind in ("view", "materialized view") and ("readable by anon" in why or "readable by authenticated" in why):
        return [("V1", {"table": clean(item["object"])})]
    if kind == "function":
        found = (("U3", "EXECUTE-able by anon"), ("U1", "EXECUTE-able by authenticated"))
        return [(flaw, {"function": clean(item["object"])}) for flaw, phrase in found if phrase in why]
    return []


def adapt(text, app, side):
    mapped = Mapped("rlsautotest")
    try:
        data = json.loads(text)
        for table in data["tables"]:
            name = clean(table["table"])
            if table.get("exposed") is True:
                mapped.add("exposed", "R1", json.dumps({"table": name, "exposed": True}), table=name)
            for footgun in table.get("footguns") or []:
                flaw = _footgun(footgun)
                if flaw:
                    mapped.add("footgun", flaw, footgun, table=name)
                else:
                    mapped.skip()
            mapped.skip(_executed_fired(table))
        for item in data["bypass_surfaces"]:
            items = _surface(item)
            for flaw, target in items:
                mapped.add(item["type"], flaw, json.dumps(item, sort_keys=True), **target)
            if not items:
                mapped.skip()
    except (ValueError, KeyError, TypeError, AttributeError, SyntaxError) as error:
        return unreadable(app, side, f"rlsautotest: output not readable ({error.__class__.__name__}: {error})")
    return mapped.run(app, side)
