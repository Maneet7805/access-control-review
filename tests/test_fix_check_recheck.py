import hashlib
import json

import pytest
from conftest import PLANTED, ROOT

from fix_check.__main__ import main
from fix_check.recheck import CannotRun, recheck

FIXTURES = ROOT / "tests" / "fixtures" / "fixcheck" / "recheck"
ROWS_01 = PLANTED / "rows-01-profiles"
TWO_TABLES = FIXTURES / "two-tables"

# The fixed twin's change for rows-01-profiles (see its fixed/ folder).
TWIN_FIX = """alter table public.profiles enable row level security;
create policy "own profile" on public.profiles for select to authenticated using (owner_id = auth.uid());
"""
LOCK_OUT = """alter table public.profiles enable row level security;
create policy "nobody" on public.profiles for select to authenticated using (false);
"""
FIX_PROFILES = TWIN_FIX
WRONG_TABLE = 'create policy "again" on public.notes for select to authenticated using (owner_id = auth.uid());\n'
NEW_LEAK = FIX_PROFILES + 'create policy "open" on public.notes for select to anon using (true);\n'
SYNTAX_ERROR = "alter table public.profiles enable row level securty;\n"


def _hash(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def _run(app, fix, tmp_path, capsys, *extra):
    """Run the command line on a fix text. Returns (exit code, output, run object). The app folder must not change."""
    fix_file = tmp_path / "fix.sql"
    fix_file.write_text(fix, encoding="utf-8")
    before = _hash(app)
    code = main(["recheck", str(app), str(fix_file), *extra])
    assert _hash(app) == before
    out = capsys.readouterr().out
    run = json.loads(out[out.index("{"):]) if "{" in out else None
    return code, out, run


def _results(run):
    return {n: c["result"] for n, c in run["conditions"].items()}


def test_the_fixed_twins_change_passes_all_four_and_exits_0(tmp_path, capsys):
    code, out, run = _run(ROWS_01, TWIN_FIX, tmp_path, capsys)
    assert code == 0
    assert _results(run) == {"1": "pass", "2": "pass", "3": "pass", "4": "pass"}
    assert run["broken"] == [] and run["works"] is True
    lines = out.splitlines()
    assert [line.split(":")[1].split(" - ")[0].strip() for line in lines[:4]] == ["PASS"] * 4
    assert lines[4] == "fix works"


def test_lock_out_fails_condition_3_and_passes_condition_2(tmp_path, capsys):
    code, out, run = _run(ROWS_01, LOCK_OUT, tmp_path, capsys)
    assert code == 1
    assert _results(run) == {"1": "pass", "2": "pass", "3": "fail", "4": "pass"}
    assert run["broken"] == [3]
    assert "broken: read profiles (no_rows_returned)" in run["conditions"]["3"]["detail"]
    assert "fix does not work" in out


def test_wrong_table_fails_condition_2_only(tmp_path, capsys):
    code, _, run = _run(TWO_TABLES, WRONG_TABLE, tmp_path, capsys, "--key", str(FIXTURES / "answer_key.json"))
    assert code == 1
    assert _results(run) == {"1": "pass", "2": "fail", "3": "pass", "4": "pass"}
    assert "R1 on profiles" in run["conditions"]["2"]["detail"]


def test_new_leak_fails_condition_4_only(tmp_path, capsys):
    code, _, run = _run(TWO_TABLES, NEW_LEAK, tmp_path, capsys, "--key", str(FIXTURES / "answer_key.json"))
    assert code == 1
    assert _results(run) == {"1": "pass", "2": "pass", "3": "pass", "4": "fail"}
    assert "R1 on notes" in run["conditions"]["4"]["detail"]


def test_syntax_error_fails_condition_1_and_the_rest_are_not_run(tmp_path, capsys):
    code, out, run = _run(ROWS_01, SYNTAX_ERROR, tmp_path, capsys)
    assert code == 1
    assert _results(run) == {"1": "fail", "2": "not run", "3": "not run", "4": "not run"}
    assert run["broken"] == [1] and run["works"] is False
    assert "NOT RUN" in out and "fix does not work" in out


def test_empty_allowed_list_passes_condition_3_and_says_so(tmp_path):
    key = json.loads((FIXTURES / "answer_key.json").read_text())
    key["two-tables"]["allowed"] = []
    run = recheck(TWO_TABLES, FIX_PROFILES, key)
    assert run["works"] is True
    assert "empty" in run["conditions"]["3"]["detail"]
    assert any("allowed list" in note for note in run["notes"])


@pytest.mark.parametrize("fix", ["", "   \n"])
def test_a_fix_that_cannot_be_added_means_the_check_cannot_run(tmp_path, capsys, fix):
    fix_file = tmp_path / "fix.sql"
    fix_file.write_text(fix)
    assert main(["recheck", str(ROWS_01), str(fix_file)]) == 2
    assert "Cannot run" in capsys.readouterr().err
    with pytest.raises(CannotRun):
        recheck(ROWS_01, fix)
