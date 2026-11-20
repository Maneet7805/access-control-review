"""docs/results.md against the saved runs: re-score them and compare every number. No Docker, no network."""
import json
import re
from pathlib import Path

import pytest

from access_review.scoring import format_table, load_key, ratio, score

ROOT = Path(__file__).parents[1]
PAGE = ROOT / "docs/results.md"
TOOLS = [("Our tool", None), ("Supabase advisors", "advisors"), ("rlsautotest", "rlsautotest"),
         ("pgrls", "pgrls"), ("Semgrep", "semgrep")]
# (page heading, key folder, our runs, baseline runs, title the scorer prints)
SETS = [("Held-out set", "heldout", "results/heldout", "results/baselines/heldout", "heldout set"),
        ("Dev set", "planted", "results/devset", "results/baselines/devset", "dev set (self-check, not accuracy)")]
NAMED = (("Missed", "missed"), ("Extra findings", "extra"), ("False alarms", "false_alarm_list"),
         ("needs_decision", "needs_decision"))


def rescore(key, ours, base, tool):
    folder = ROOT / (base + "/" + tool if tool else ours)
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))]
    return score(runs, load_key(ROOT / key / "answer_key.json"))


def expected_cells(r):
    return {"Recall": ratio(r["found"], r["planted"]), "Precision": ratio(r["matched"], r["proved"]),
            "False alarms": str(r["false_alarms"]),
            "False-alarm rate": ratio(r["clean_runs_with_alarm"], r["clean_runs"]),
            "Extra findings": str(len(r["extra"])), "Not checkable": str(r["not_checkable"]),
            "Probe errors": str(r["probe_errors"]), "needs_decision": str(len(r["needs_decision"]))}


def section(text, heading, level="## "):
    """Lines under `heading` up to the next heading of any level."""
    lines = text.splitlines()
    start = lines.index(level + heading) + 1
    return lines[start:next((i for i in range(start, len(lines)) if lines[i].startswith("#")), len(lines))]


def mismatches(text):
    """Every place where the page differs from the re-scored runs."""
    bad = []
    if text.index("## Held-out set") > text.index("## Dev set"):
        bad.append("dev set comes before held-out set")
    for name, key, ours, base, _ in SETS:
        rows = [[c.strip() for c in line.strip("|").split("|")] for line in section(text, name) if line.startswith("|")]
        header = rows[0]
        body = {row[0]: dict(zip(header, row, strict=True)) for row in rows[2:]}
        if set(body) != {label for label, _ in TOOLS}:
            bad.append(f"{name}: rows are {sorted(body)}")
        for label, tool in TOOLS:
            r = rescore(key, ours, base, tool)
            for column, value in expected_cells(r).items():
                shown = body.get(label, {}).get(column)
                if shown != value:
                    bad.append(f"{name}, {label}, {column}: page {shown!r}, re-scored {value!r}")
            listed = {line[2:] for line in section(text, f"{name}: {label}", "#### ") if line.startswith("- ")}
            want = {f"{title}: {item}" for title, field in NAMED for item in r[field]} or {"Nothing to list."}
            if listed != want:
                bad.append(f"{name}, {label}: named items differ: {sorted(listed ^ want)}")
    return bad


def test_every_number_matches_the_rescored_runs():
    assert mismatches(PAGE.read_text(encoding="utf-8")) == []


def test_every_row_has_a_needs_decision_count():
    text = PAGE.read_text(encoding="utf-8")
    for name, *_ in SETS:
        rows = [line for line in section(text, name) if line.startswith("| ") and "---" not in line][1:]
        assert len(rows) == len(TOOLS)
        assert all(re.fullmatch(r"\d+", row.strip("|").split("|")[-1].strip()) for row in rows)


@pytest.mark.parametrize("name,key,ours,base,title", SETS)
def test_scores_equal_the_saved_score_files(name, key, ours, base, title):
    """The re-scored table is the same text the run scripts saved next to the raw outputs."""
    saved = {None: ROOT / ("results/devset-score.txt" if key == "planted" else ours + "/score.txt")}
    saved.update({tool: ROOT / base / f"score-{tool}.txt" for _, tool in TOOLS if tool})
    for _, tool in TOOLS:
        assert format_table(title, rescore(key, ours, base, tool)).splitlines() == \
            saved[tool].read_text(encoding="utf-8").splitlines()


def test_negative_control_one_changed_number_fails():
    text = PAGE.read_text(encoding="utf-8")
    assert "12/15 (0.80)" in text
    assert mismatches(text.replace("12/15 (0.80)", "13/15 (0.87)", 1))


def test_negative_control_a_changed_name_fails():
    text = PAGE.read_text(encoding="utf-8")
    assert mismatches(text.replace("Missed: plant-swaps/vulnerable", "Missed: plant-swaps/fixed", 1))


def test_wording():
    text = PAGE.read_text(encoding="utf-8")
    assert "secure" not in text.lower()
    assert "No violation found under this test." in text
    assert "reported, not executed" in text and "| executed |" in text
    assert "pooled" in text and not re.search(r"\|\s*(total|average|all sets)\s*\|", text, re.I)
