"""Fail if anything frozen changed after the held-out run (docs/ROADMAP.md M5.5).

Usage: python scripts/check_no_tuning.py [--repo DIR]
Reads the commit in results/heldout/RUN.txt and asks git what changed since. Exit 0 = nothing tuned,
1 = a frozen file changed or a held-out result was modified or deleted (each path is printed), 2 = cannot check.
Needs full git history, so it is not part of CI.
"""
import argparse
import subprocess  # noqa: S404 - fixed argument lists, no shell
import sys
from pathlib import Path

FROZEN = [
    "src/access_review/", "planted/", "heldout/", "docs/EVALUATION.md", "docs/baselines.md",
    "scripts/run_devset.py", "scripts/run_baselines.py", "tests/test_adapters.py", "tests/fixtures/baselines/",
]
RESULTS = ["results/heldout/", "results/baselines/heldout/"]


def _git(repo, *args):
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)  # noqa: S603,S607
    if done.returncode:
        sys.exit(f"cannot check: git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout.splitlines()


def offenders(repo):
    """Return (commit, paths that break the rule)."""
    run_txt = Path(repo) / "results/heldout/RUN.txt"
    first = run_txt.read_text(encoding="utf-8").splitlines()[0] if run_txt.is_file() else ""
    if not first.startswith("commit: "):
        sys.exit("cannot check: results/heldout/RUN.txt has no 'commit: <hash>' first line")
    commit = first.split()[1]
    # --no-renames: a moved file shows as delete plus add, so a moved result still counts as deleted.
    # No HEAD: compares with the working tree, so uncommitted edits to tracked files count too.
    base = ["diff", "--name-only", "--no-renames", commit, "--"]
    bad = _git(repo, *base, *FROZEN)
    bad += _git(repo, *base[:2], "--diff-filter=MDT", *base[2:], *RESULTS)
    return commit, sorted(set(bad))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=Path(__file__).resolve().parents[1])
    commit, bad = offenders(ap.parse_args(argv).repo)
    print(f"checked against {commit}")
    for path in bad:
        print(f"CHANGED AFTER HELD-OUT RUN: {path}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
