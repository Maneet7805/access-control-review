import json

from conftest import PLANTED, ROOT

from fix_check.__main__ import main
from fix_check.run import apps_in_plan

FIXES = ROOT / "fixes" / "reference"
LOCK_OUT = """alter table public.profiles enable row level security;
create policy "nobody" on public.profiles for select to authenticated using (false);
"""


def _run(tmp_path, capsys, *extra):
    code = main(["run", "reference", "--out", str(tmp_path / "out"), *extra])
    return code, capsys.readouterr().out


def test_the_plan_has_15_apps_and_each_has_a_reference_fix_file():
    apps = apps_in_plan(PLANTED)
    assert len(apps) == 15  # the plan's reference total (docs/fixcheck-plan.md section 3)
    assert sorted(p.stem for p in FIXES.glob("*.sql")) == sorted(apps)


def test_a_missing_fix_file_is_counted_and_fails_condition_1(tmp_path, capsys):
    empty = tmp_path / "none"
    empty.mkdir()
    code, out = _run(tmp_path, capsys, "--fixes", str(empty))
    assert code == 0
    assert "Reference: 15 attempts, 0 of 15 succeeded, broke 1: 15, broke 2: 0, broke 3: 0, broke 4: 0" in out
    run = json.loads((tmp_path / "out" / "rows-01-profiles__1.json").read_text())
    assert run["broken"] == [1] and run["conditions"]["2"]["result"] == "not run"
    assert len(list((tmp_path / "out").glob("*__1.json"))) == 15


def test_an_empty_fix_file_is_counted_and_fails_condition_1(tmp_path, capsys):
    fixes = tmp_path / "fixes"
    fixes.mkdir(parents=True)
    (fixes / "rows-01-profiles.sql").write_text("", encoding="utf-8")
    _run(tmp_path, capsys, "--fixes", str(fixes))
    run = json.loads((tmp_path / "out" / "rows-01-profiles__1.json").read_text())
    assert run["broken"] == [1] and "refused" in run["conditions"]["1"]["detail"]


def _one_app(tmp_path, fix, capsys):
    """Run the real runner on rows-01-profiles only, with the given fix text. Returns the run object."""
    from fix_check.run import run_reference
    fixes = tmp_path / "fixes"
    fixes.mkdir(parents=True)
    (fixes / "rows-01-profiles.sql").write_text(fix, encoding="utf-8")
    runs = run_reference(tmp_path / "out", fixes, PLANTED, apps=["rows-01-profiles"])
    capsys.readouterr()
    return runs[0]


def test_the_reference_fix_passes_and_a_lock_out_in_a_scratch_copy_fails_condition_3(tmp_path, capsys):
    ok = _one_app(tmp_path / "a", (FIXES / "rows-01-profiles.sql").read_text(encoding="utf-8"), capsys)
    assert ok["works"] and ok["broken"] == []
    bad = _one_app(tmp_path / "b", LOCK_OUT, capsys)
    assert bad["broken"] == [3]
