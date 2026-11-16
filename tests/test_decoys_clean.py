"""M3.8: the false-alarm test. Clean apps give no finding; decoys never give a proved one."""
import json

import pytest
from conftest import PLANTED

from access_review.cli import main
from access_review.report import NO_VIOLATION

ANSWER_KEY = json.loads((PLANTED / "answer_key.json").read_text())
CLEAN = ["clean-01-all-correct", "clean-02-all-correct-different-style"]
DECOYS = ["decoy-02-public-profile-read", "decoy-03-shared-team-table"]


def _review(app_dir, tmp_path):
    out = tmp_path / "report.md"
    return main(["review", str(app_dir), "--out", str(out)]), out.read_text(encoding="utf-8")


@pytest.mark.parametrize("app", CLEAN)
def test_a_clean_app_has_no_finding(app, tmp_path):
    code, report = _review(PLANTED / app / "migrations", tmp_path)
    assert code == 0 and NO_VIOLATION in report and "could not run" not in report


@pytest.mark.parametrize("app", DECOYS)
def test_a_decoy_never_gives_a_proved_finding(app, tmp_path):
    code, report = _review(PLANTED / app / "migrations", tmp_path)
    assert code == 0 and "Proved" not in report and "could not run" not in report


def test_a_public_profile_page_is_left_for_the_developer_to_decide(tmp_path):
    _, report = _review(PLANTED / "decoy-02-public-profile-read" / "migrations", tmp_path)
    assert "Needs your decision" in report


def test_a_team_table_shared_on_purpose_gives_no_finding(tmp_path):
    _, report = _review(PLANTED / "decoy-03-shared-team-table" / "migrations", tmp_path)
    assert NO_VIOLATION in report


@pytest.mark.parametrize("app,flaw", [("clean-01-all-correct", "disable row level security"),
                                      ("clean-02-all-correct-different-style", "disable row level security")])
def test_the_same_app_with_a_flaw_is_caught(app, flaw, tmp_path):
    # Negative control: the clean result is not because the tests are blind. Switch row security off and it fires.
    table = "notes" if app == "clean-01-all-correct" else "tasks"
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    sql = (PLANTED / app / "migrations" / "001_init.sql").read_text(encoding="utf-8")
    (app_dir / "001_init.sql").write_text(f"{sql}\nalter table public.{table} {flaw};\n", encoding="utf-8")
    code, report = _review(app_dir, tmp_path)
    assert code == 1 and "Proved" in report


def test_the_key_marks_decoys_and_lists_no_flaw_for_these_apps():
    for app in CLEAN + DECOYS:
        entry = ANSWER_KEY[app]
        assert entry["flaws_vulnerable"] == [] and entry["flaws_fixed"] == []
        assert entry["decoy"] == (app in DECOYS)
