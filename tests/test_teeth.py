"""M3.9: the tests must have teeth. Swap each probe for a broken one and the planted-app tests must fail.

Each case runs the planted-app tests in a separate pytest, with one probe replaced (see teeth_plugin.py), and
expects a plain test failure: exit code 1, not a crash. A control run with no broken probe must pass.
"""
import os
import subprocess
import sys

import pytest
from conftest import ROOT

FILE_OF = {
    "visitor_reads_rows": "test_planted.py",
    "user_reads_rows": "test_planted.py",
    "visitor_inserts_row": "test_writes.py",
    "user_inserts_row_for_other": "test_writes.py",
    "user_updates_rows": "test_writes.py",
    "user_deletes_rows": "test_writes.py",
    "user_changes_row_owner": "test_writes.py",
    "user_reads_view": "test_writes.py",
    "user_writes_protected_columns": "test_writes.py",
    "visitor_calls_function": "test_functions.py",
    "user_calls_function": "test_functions.py",
    "visitor_reads_private_columns": "test_private_columns.py",
    "user_reads_private_columns": "test_private_columns.py",
}


def _run(teeth, test_file):
    env = {**os.environ, "TEETH": teeth, "PYTHONPATH": str(ROOT / "tests")}
    return subprocess.run(
        [sys.executable, "-m", "pytest", f"tests/{test_file}", "-k", "answer_key", "-x", "-q", "-p", "teeth_plugin",
         "-p", "no:cacheprovider"], cwd=ROOT, env=env, capture_output=True, text=True)


@pytest.mark.parametrize("probe,test_file", sorted(FILE_OF.items()))
@pytest.mark.parametrize("mode", ["clean", "leak"])
def test_a_broken_probe_is_caught(probe, test_file, mode):
    result = _run(f"{probe}:{mode}", test_file)
    assert result.returncode == 1 and "1 failed" in result.stdout, result.stdout[-1500:]


def test_the_swap_itself_does_not_break_the_tests():
    # Control: with no probe replaced the same selection passes, so the failures above come from the broken probes.
    result = _run("", "test_planted.py")
    assert result.returncode == 0, result.stdout[-1500:]
