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


def test_vulnerable_app_exits_1_with_exactly_its_five_findings(tmp_path):
    # Row security is off on rows-01: a user can read others' rows (R2), a visitor and a user can add rows (R3, R4),
    # and a user can change and delete others' rows (R5, R6). The key lists R5 and R6 only after the follow-up key PR.
    code, report = _run("rows-01-profiles/vulnerable", tmp_path)
    assert code == 1
    assert report.count("\n## ") == 5 and "5 problem(s) proved" in report
    for wording in ("read rows that belong to other users", "visitor who is not signed in can add rows",
                    "names someone else as its owner", "can change rows that belong to other users",
                    "can delete rows that belong to other users"):
        assert wording in report


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


def _app(tmp_path, sql):
    (tmp_path / "001.sql").write_bytes(sql.encode())
    return tmp_path


def test_table_with_a_newline_in_its_name_is_probed_as_one_table(tmp_path):
    from access_review.cli import review
    from access_review.sandbox import sandbox

    table = 'public."a\nb"'
    migrations = _app(tmp_path, f"create table {table} (id int); insert into {table} values (1);"
                                f"grant select on {table} to anon; alter table {table} enable row level security;"
                                f"create policy open_read on {table} for select to anon using (true);")
    with sandbox(migrations, baseline=True) as box:
        findings, _ = review(box)
    assert [(f.flaw_id, f.table) for f in findings] == [("R1", "a\nb")]


def test_report_says_when_the_app_has_too_few_users_to_act_as(tmp_path):
    out = tmp_path / "report.md"
    migrations = tmp_path / "app"
    migrations.mkdir()
    _app(migrations, "create table public.t (id int);")
    assert main(["review", str(migrations), "--out", str(out)]) == 0
    assert "fewer than 2 users" in out.read_text(encoding="utf-8")


def test_no_too_few_users_note_when_the_app_has_two(tmp_path):
    # Negative control: the planted apps seed two users.
    _, report = _run("rows-01-profiles/fixed", tmp_path)
    assert "fewer than 2 users" not in report
