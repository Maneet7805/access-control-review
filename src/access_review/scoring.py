"""Score findings against the answer key, by the frozen rules in docs/EVALUATION.md.

Reads findings JSON and the key only. It never imports probes, rules or the sandbox.
A run is a dict: {"app", "side", "not_checkable": bool, "probe_errors": bool, "findings": [Finding.to_dict()]}.
The app and side come from the folder the run was made on, never from a finding.
"""
import json
from pathlib import Path

TARGET_FIELDS = ("table", "column", "function")


def _expected(key, run):
    entry = key.get(run["app"])
    if entry is None:  # not in the key: not scored
        return None
    return entry["flaws_fixed" if run["side"] == "fixed" else "flaws_vulnerable"]


def _target(item):
    return tuple(item.get(field) for field in TARGET_FIELDS)


def _matches(flaw, finding):
    return flaw["flaw_id"] == finding["flaw_id"] and all(
        finding.get(field) == flaw[field] for field in TARGET_FIELDS if field in flaw)


def _name(item):
    return f'{item["flaw_id"]} on ' + ", ".join(f"{f} {item[f]}" for f in TARGET_FIELDS if item.get(f))


def score(runs, key):
    """Score one set of runs. Returns a dict of counts and lists; ratios are made by `ratio`."""
    planted = found = proved_total = matched = false_alarms = clean_runs = clean_alarm_runs = 0
    not_checkable = probe_errors = scored_runs = 0
    extra, false_alarm_list, needs_decision, missed = [], [], [], []
    for run in runs:
        expected = _expected(key, run)
        if expected is None:
            continue
        label = f'{run["app"]}/{run["side"]}'
        scored_runs += 1
        not_checkable += bool(run.get("not_checkable"))
        probe_errors += bool(run.get("probe_errors"))
        findings = [] if run.get("not_checkable") else run["findings"]
        proved, seen = [], set()
        for finding in findings:
            if finding["status"] == "needs_decision":
                needs_decision.append(f"{label}: {_name(finding)}")
            elif finding["status"] == "proved":
                identity = (finding["flaw_id"], *_target(finding))
                if identity not in seen:  # duplicates count once
                    seen.add(identity)
                    proved.append(finding)
        proved_total += len(proved)
        for flaw in expected:
            planted += 1
            if any(_matches(flaw, finding) for finding in proved):
                found += 1
            else:
                missed.append(f"{label}: {_name(flaw)}")
        unmatched = [f for f in proved if not any(_matches(flaw, f) for flaw in expected)]
        matched += len(proved) - len(unmatched)
        if expected:
            extra += [f"{label}: {_name(f)}" for f in unmatched]
        else:
            clean_runs += 1
            false_alarms += len(unmatched)
            clean_alarm_runs += bool(unmatched)
            false_alarm_list += [f"{label}: {_name(f)}" for f in unmatched]
    return {"runs": scored_runs, "planted": planted, "found": found, "proved": proved_total, "matched": matched,
            "clean_runs": clean_runs, "false_alarms": false_alarms, "clean_runs_with_alarm": clean_alarm_runs,
            "not_checkable": not_checkable, "probe_errors": probe_errors, "missed": missed, "extra": extra,
            "false_alarm_list": false_alarm_list, "needs_decision": needs_decision}


def ratio(top, bottom):
    """'k/n (0.50)', or 'n/a' when there is nothing to divide by."""
    return f"{top}/{bottom} ({top / bottom:.2f})" if bottom else "n/a"


def format_table(name, result):
    lines = [f"Score: {name}",
             f'  Recall:            {ratio(result["found"], result["planted"])}',
             f'  Precision:         {ratio(result["matched"], result["proved"])}',
             f'  False alarms:      {result["false_alarms"]}',
             f'  False-alarm rate:  {ratio(result["clean_runs_with_alarm"], result["clean_runs"])}',
             f'  Extra findings:    {len(result["extra"])}',
             f'  Not checkable:     {result["not_checkable"]}',
             f'  Probe errors:      {result["probe_errors"]}',
             f'  needs_decision:    {len(result["needs_decision"])}']
    for title, items in (("Missed", "missed"), ("Extra findings", "extra"),
                         ("False alarms", "false_alarm_list"), ("needs_decision", "needs_decision")):
        lines += [f"  {title}: " + item for item in result[items]]
    return "\n".join(lines)


def load_key(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
