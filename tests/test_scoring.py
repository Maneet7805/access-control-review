"""Tests for the scoring module. Hand-written findings, hand-computed expected numbers. No Docker."""
import ast
import json
from pathlib import Path

from access_review import scoring
from access_review.scoring import format_table, load_key, ratio, score

KEY = {
    "app-a": {"flaws_vulnerable": [{"flaw_id": "R2", "table": "p"}, {"flaw_id": "R5", "table": "p"}],
              "flaws_fixed": []},
    "app-b": {"flaws_vulnerable": [], "flaws_fixed": []},
    "app-c": {"flaws_vulnerable": [], "flaws_fixed": []},
}


def f(flaw_id, table=None, status="proved", actor="user-a", column=None, function=None):
    return {"flaw_id": flaw_id, "table": table, "status": status, "actor": actor,
            "column": column, "function": function}


def run(app, side, findings=(), not_checkable=False, probe_errors=False):
    return {"app": app, "side": side, "findings": list(findings),
            "not_checkable": not_checkable, "probe_errors": probe_errors}


def example(with_r2=True):
    """The worked example of docs/EVALUATION.md section 5."""
    return [
        run("app-a", "vulnerable",
            ([f("R2", "p")] if with_r2 else []) + [f("R6", "p"), f("R1", "q", "needs_decision")]),
        run("app-a", "fixed"),
        run("app-b", "migrations", [f("R1", "x", "needs_decision")]),
        run("app-c", "migrations", [f("R1", "n")]),
    ]


def test_worked_example():
    r = score(example(), KEY)
    assert (r["found"], r["planted"]) == (1, 2)
    assert (r["matched"], r["proved"]) == (1, 3)
    assert r["extra"] == ["app-a/vulnerable: R6 on table p"]
    assert (r["false_alarms"], r["clean_runs_with_alarm"], r["clean_runs"]) == (1, 1, 3)
    assert len(r["needs_decision"]) == 2


def test_negative_control_dropping_a_finding_lowers_recall_and_precision():
    r = score(example(with_r2=False), KEY)
    assert (r["found"], r["planted"]) == (0, 2)
    assert (r["matched"], r["proved"]) == (0, 2)


def test_zero_denominators_are_na():
    r = score([run("app-b", "migrations")], KEY)
    assert ratio(r["found"], r["planted"]) == "n/a"
    assert ratio(r["matched"], r["proved"]) == "n/a"
    assert ratio(r["clean_runs_with_alarm"], r["clean_runs"]) == "0/1 (0.00)"
    assert ratio(*(lambda x: (x["clean_runs_with_alarm"], x["clean_runs"]))(score([], KEY))) == "n/a"
    assert "Recall:            n/a" in format_table("t", r)


def test_duplicates_count_once_but_other_targets_do_not():
    r = score([run("app-a", "vulnerable", [f("R2", "p"), f("R2", "p", actor="user-b"), f("R2", "other")])], KEY)
    assert (r["matched"], r["proved"]) == (1, 2)
    assert r["found"] == 1


def test_flawed_run_not_checkable_counts_as_misses():
    r = score([run("app-a", "vulnerable", [f("R2", "p")], not_checkable=True)], KEY)
    assert (r["found"], r["planted"], r["proved"], r["not_checkable"]) == (0, 2, 0, 1)


def test_clean_run_not_checkable_stays_in_totals_without_alarm():
    r = score([run("app-b", "migrations", not_checkable=True)], KEY)
    assert (r["clean_runs"], r["false_alarms"], r["not_checkable"]) == (1, 0, 1)


def test_needs_decision_for_a_planted_flaw_is_a_miss_and_in_the_tally():
    r = score([run("app-a", "vulnerable", [f("R2", "p", "needs_decision"), f("R5", "p")])], KEY)
    assert (r["found"], r["planted"]) == (1, 2)
    assert (r["matched"], r["proved"]) == (1, 1)
    assert r["needs_decision"] == ["app-a/vulnerable: R2 on table p"]


def test_proved_finding_on_fixed_side_never_matches_the_vulnerable_entry():
    r = score([run("app-a", "fixed", [f("R2", "p")])], KEY)
    assert (r["false_alarms"], r["matched"], r["proved"]) == (1, 0, 1)


def test_column_and_function_targets_and_unnamed_fields_ignored():
    key = {"x": {"flaws_vulnerable": [{"flaw_id": "C1", "table": "m", "column": "role"},
                                      {"flaw_id": "U1", "function": "fn"}], "flaws_fixed": []}}
    wrong_column = f("C1", "m", column="other")
    r = score([run("x", "vulnerable", [wrong_column, f("U1", function="fn", table="ignored")])], key)
    assert (r["found"], r["planted"]) == (1, 2)


def test_probe_errors_counted_and_apps_outside_key_ignored():
    r = score([run("app-a", "vulnerable", probe_errors=True), run("hostile", "migrations", [f("R1", "z")])], KEY)
    assert (r["probe_errors"], r["runs"], r["proved"]) == (1, 1, 0)


def test_label_comes_from_the_run_not_the_finding():
    finding = {**f("R2", "p"), "app": "app-b", "side": "fixed"}
    r = score([run("app-a", "vulnerable", [finding])], KEY)
    assert r["found"] == 1


def test_table_text_lists_counts_and_names():
    text = format_table("dev", score(example(), KEY))
    assert "Recall:            1/2 (0.50)" in text
    assert "False-alarm rate:  1/3 (0.33)" in text
    assert "needs_decision:    2" in text
    assert "Extra findings: app-a/vulnerable: R6 on table p" in text


def test_real_key_loads():
    assert "rows-01-profiles" in load_key(Path(__file__).parent.parent / "planted" / "answer_key.json")


def test_scoring_imports_no_probes_rules_or_sandbox():
    tree = ast.parse(Path(scoring.__file__).read_text(encoding="utf-8"))
    names = {n.names[0].name if isinstance(n, ast.Import) else (n.module or "") for n in ast.walk(tree)
             if isinstance(n, (ast.Import, ast.ImportFrom))}
    assert names <= {"json", "pathlib", "sys"}, names

PLANTED = Path(__file__).parent.parent / "planted"


def _save_perfect_runs(folder):
    """Saved runs that find exactly the key's flaws, one file per scored folder."""
    key = load_key(PLANTED / "answer_key.json")
    for app, side, _ in scoring.expected_runs(PLANTED):
        flaws = key[app]["flaws_fixed" if side == "fixed" else "flaws_vulnerable"]
        findings = [{**{k: v for k, v in x.items() if k in ("flaw_id", "table", "column", "function")},
                     "status": "proved"} for x in flaws]
        (folder / f"{app}__{side}.json").write_text(json.dumps(run(app, side, findings)), encoding="utf-8")


def test_expected_runs_labels_come_from_folders():
    runs = {(app, side) for app, side, _ in scoring.expected_runs(PLANTED)}
    assert ("rows-01-profiles", "fixed") in runs and ("decoy-01-public-posts", "migrations") in runs
    assert ("rows-03-locked-out", "vulnerable") not in runs and not any(a == "hostile-01-callout" for a, _ in runs)


def test_main_scores_saved_runs_and_refuses_a_missing_one(tmp_path, capsys):
    _save_perfect_runs(tmp_path)
    assert scoring.main([str(PLANTED), "--runs", str(tmp_path)]) == 0
    assert "Recall:            " in capsys.readouterr().out
    (tmp_path / "rows-01-profiles__fixed.json").unlink()  # negative control
    assert scoring.main([str(PLANTED), "--runs", str(tmp_path)]) == 2
