"""Shared pieces of the baseline adapters: the run object and the mapped-finding builder.

An adapter takes the raw output text plus the app and side and returns the run object that
scripts/run_devset.py writes: app, side, not_checkable, probe_errors, findings, notes.
"""
from access_review.evidence import Evidence
from access_review.findings import Finding


def unreadable(app, side, reason):
    """Output that cannot be read. Never an empty result that looks clean."""
    return {"app": app, "side": side, "not_checkable": True, "probe_errors": False, "findings": [], "notes": [reason]}


def clean(name):
    """A table or function name as the mapping rules read it: no quotes, no `public.`, cut at `(`."""
    name = str(name).replace('"', "").strip()
    return name.removeprefix("public.").split("(")[0].strip()


class Mapped:
    """Collects mapped findings (one per flaw id and target) and counts unmapped items."""

    def __init__(self, tool):
        self.tool = tool
        self.found = {}
        self.unmapped = 0

    def add(self, rule, flaw_id, line, **target):
        """A mapped item. `line` is the raw output line kept as proof. Same flaw and target is one finding."""
        evidence = Evidence(probe=f"{self.tool}:{rule}", actor=f"baseline:{self.tool}", statement=line, result="ok")
        key = (flaw_id, *sorted(target.items()))
        if key in self.found:
            self.found[key].proof.append(evidence)
            return
        name = "/".join(str(v) for v in target.values())
        self.found[key] = Finding(
            id=f"{self.tool}-{flaw_id}-{name}", flaw_id=flaw_id, actor=f"baseline:{self.tool}", proof=[evidence],
            explanation=f"{self.tool} reported rule {rule}, mapped to {flaw_id} by docs/baselines.md section 3. "
                        "Reported by the tool, not executed by this project.",
            fix="The baseline gives no fix in this shape; see the raw output.", status="proved", **target)

    def skip(self, count=1):
        self.unmapped += count

    def run(self, app, side, extra_notes=()):
        notes = [f"{self.tool}: {self.unmapped} unmapped item(s) not emitted", *extra_notes]
        return {"app": app, "side": side, "not_checkable": False, "probe_errors": False,
                "findings": [f.to_dict() for f in self.found.values()], "notes": notes}
