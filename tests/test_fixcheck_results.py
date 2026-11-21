"""docs/fixcheck-results.md against the saved runs: recount every number and compare. No Docker, no network."""
import json
import re
from pathlib import Path

from fix_check.run import apps_in_plan

ROOT = Path(__file__).parents[1]
PAGE = ROOT / "docs/fixcheck-results.md"
RESULTS = ROOT / "results/fixcheck"
# (page heading, row label, folder, attempts per app in docs/fixcheck-plan.md section 3)
SOURCES = [("Reference fixes", "Reference", "reference", 1), ("AI fixes", "AI", "ai", 3)]


def load(folder):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((RESULTS / folder).glob("*.json"))]


def section(text, heading):
    lines = text.splitlines()
    start = lines.index("## " + heading) + 1
    return lines[start:next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))]


def expected_row(label, runs):
    n, ok = len(runs), sum(r["works"] for r in runs)
    broke = [sum(c in r["broken"] for r in runs) for c in (1, 2, 3, 4)]
    return ["| " + " | ".join([label, str(n), f"{ok} of {n} ({round(100 * ok / n)}%)", *map(str, broke)]) + " |"]


def expected_failures(runs):
    failed = [r for r in runs if not r["works"]]
    lines = [f'- {r["app"]}, attempt {r["attempt"]}: broke {"+".join(map(str, r["broken"]))}' for r in failed]
    return sorted(lines) or ["- None."]


def problems(text):
    """Every way the page differs from the recount. An empty list means every number matches."""
    found = []
    if re.search("secure", text, re.I):
        found.append("the page contains the word secure")
    n_apps = len(apps_in_plan(ROOT / "planted"))
    for heading, label, folder, per_app in SOURCES:
        runs = load(folder)
        if len(runs) != n_apps * per_app:
            found.append(f"{label}: {len(runs)} saved runs, plan says {n_apps * per_app}")
        if any("cannot_run" in r for r in runs):
            found.append(f"{label}: an attempt could not be run")
        lines = section(text, heading)
        rows = [x for x in lines if x.startswith("| " + label + " |")]
        if rows != expected_row(label, runs):
            found.append(f"{label}: table row {rows} != {expected_row(label, runs)}")
        got = sorted(x for x in lines if x.startswith("- ") and ", attempt " in x or x == "- None.")
        if got != expected_failures(runs):
            found.append(f"{label}: failed attempts {got} != {expected_failures(runs)}")
    ai = len(load("ai"))
    if f"The AI source is {ai} attempts" not in text:
        found.append("the page does not state the AI attempt count")
    model = re.search(r"^Model: (\S+)", (RESULTS / "RUN.txt").read_text(encoding="utf-8"), re.M).group(1)
    if model not in text:
        found.append("the page does not name the model in RUN.txt")
    return found


def test_page_matches_the_saved_runs():
    assert problems(PAGE.read_text(encoding="utf-8")) == []


def test_launch_fault_runs_are_not_counted():
    fault = list((RESULTS / "launch-fault").glob("*.json"))
    assert fault, "the launch-fault evidence is missing"
    assert len(load("ai")) == 45 == len(fault) == len(apps_in_plan(ROOT / "planted")) * 3
    for p in fault:
        r = json.loads(p.read_text(encoding="utf-8"))
        assert not r["works"] and "could not be asked" in " ".join(r["notes"])
    assert "results/fixcheck/launch-fault/" in PAGE.read_text(encoding="utf-8")


def test_negative_control_a_changed_number_fails():
    text = PAGE.read_text(encoding="utf-8")
    assert "| AI | 45 | 33 of 45 (73%) | 0 | 6 | 9 | 3 |" in text
    for old, new in [("| 0 | 6 | 9 | 3 |", "| 0 | 6 | 9 | 4 |"), ("33 of 45", "34 of 45"),
                     ("writes-01-visitor-insert, attempt 2: broke 2", "writes-01-visitor-insert, attempt 2: broke 3")]:
        assert old in text
        assert problems(text.replace(old, new, 1)), old
    assert problems(text + "\nThis app is secure.")
