"""check_no_tuning.py on a small temporary git repo: no Docker, no network."""
import importlib.util
import subprocess  # noqa: S404 - fixed argument lists, no shell
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts/check_no_tuning.py"
SPEC = importlib.util.spec_from_file_location("check_no_tuning", SCRIPT)
cnt = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cnt)


def git(repo, *args):
    done = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],  # noqa: S603,S607
                          capture_output=True, text=True, check=True)
    return done.stdout.strip()


def put(repo, name, text):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    """Frozen files and a held-out result at commit A; RUN.txt names A and is added after it."""
    git(tmp_path, "init", "-q")
    put(tmp_path, "src/access_review/probes.py", "v1\n")
    put(tmp_path, "docs/EVALUATION.md", "v1\n")
    put(tmp_path, "results/heldout/a.json", "v1\n")
    put(tmp_path, "docs/ROADMAP.md", "v1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "frozen")
    put(tmp_path, "results/heldout/RUN.txt", f"commit: {git(tmp_path, 'rev-parse', 'HEAD')}\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "run")
    return tmp_path


def run(repo, capsys):
    code = cnt.main(["--repo", str(repo)])
    return code, capsys.readouterr().out


def edit_and_commit(repo, name, text):
    put(repo, name, text)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "later")


def test_clean_repo_passes_and_prints_commit(repo, capsys):
    code, out = run(repo, capsys)
    assert code == 0 and "checked against " + git(repo, "rev-parse", "HEAD~1") in out


def test_unfrozen_edit_and_new_result_are_allowed(repo, capsys):
    edit_and_commit(repo, "docs/ROADMAP.md", "v2\n")
    edit_and_commit(repo, "results/heldout/new.json", "x\n")
    assert run(repo, capsys)[0] == 0


@pytest.mark.parametrize("name", ["src/access_review/probes.py", "docs/EVALUATION.md"])
def test_frozen_file_edit_fails(repo, capsys, name):  # negative control
    edit_and_commit(repo, name, "tuned\n")
    code, out = run(repo, capsys)
    assert code == 1 and name in out


def test_new_file_in_frozen_folder_fails(repo, capsys):
    edit_and_commit(repo, "src/access_review/extra.py", "x\n")
    assert run(repo, capsys)[0] == 1


def test_modified_result_fails(repo, capsys):
    edit_and_commit(repo, "results/heldout/a.json", "v2\n")
    code, out = run(repo, capsys)
    assert code == 1 and "results/heldout/a.json" in out


def test_deleted_result_fails(repo, capsys):
    git(repo, "rm", "-q", "results/heldout/a.json")
    git(repo, "commit", "-qm", "rm")
    assert run(repo, capsys)[0] == 1


def test_missing_run_txt_cannot_check(tmp_path):
    with pytest.raises(SystemExit) as e:
        cnt.offenders(tmp_path)
    assert "RUN.txt" in str(e.value)
