import importlib.util
import sys

from conftest import ROOT

spec = importlib.util.spec_from_file_location("check", ROOT / "scripts" / "check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def test_run_reports_pass_for_a_command_that_succeeds(capsys):
    assert check.run("good", [sys.executable, "-c", "pass"]) is True
    assert capsys.readouterr().out.startswith("PASS  good")


def test_run_reports_fail_for_a_command_that_fails(capsys):
    assert check.run("bad", [sys.executable, "-c", "raise SystemExit(1)"]) is False
    assert capsys.readouterr().out.startswith("FAIL  bad")


def test_main_fails_if_any_check_fails(monkeypatch):
    monkeypatch.setattr(check, "CHECKS", {"good": ["-c", "pass"], "bad": ["-c", "raise SystemExit(1)"]})
    assert check.main() == 1
