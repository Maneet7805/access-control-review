import subprocess
import sys

from conftest import PLANTED, ROOT

from access_review.cli import main
from access_review.report import NO_VIOLATION

BROKEN = ROOT / "tests" / "fixtures" / "broken"


def _run(app, tmp_path):
    out = tmp_path / "report.md"
    code = main(["review", str(PLANTED / app / "migrations"), "--out", str(out)])
    return code, out.read_text(encoding="utf-8") if out.exists() else None


def test_vulnerable_app_exits_1_with_one_finding(tmp_path):
    code, report = _run("rows-01-profiles/vulnerable", tmp_path)
    assert code == 1
    assert report.count("\n## ") == 1 and "1 problem(s) proved" in report


def test_fixed_twin_exits_0_with_the_no_violation_sentence(tmp_path):
    # Negative control: same command, fixed app.
    code, report = _run("rows-01-profiles/fixed", tmp_path)
    assert code == 0 and NO_VIOLATION in report


def test_broken_migration_exits_2_with_the_reason_and_no_report(tmp_path, capsys):
    out = tmp_path / "report.md"
    assert main(["review", str(BROKEN / "syntax_error"), "--out", str(out)]) == 2
    assert "001.sql, line 3" in capsys.readouterr().err
    assert not out.exists()


def test_public_table_by_design_is_reported_for_decision_but_does_not_fail(tmp_path):
    code, report = _run("decoy-01-public-posts", tmp_path)
    assert code == 0 and "Needs your decision" in report and "Proved" not in report


def test_python_dash_m_runs_the_same_command(tmp_path):
    out = tmp_path / "report.md"
    result = subprocess.run(
        [sys.executable, "-m", "access_review", "review", str(PLANTED / "rows-02-profiles-all-authenticated"
                                                                / "vulnerable" / "migrations"), "--out", str(out)],
        capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 1 and out.exists()
