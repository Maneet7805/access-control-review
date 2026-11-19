"""Run one baseline tool on every scored folder of an apps folder; save its raw output and the run object.

Usage: python scripts/run_baselines.py <folder> --tool semgrep|advisors|rlsautotest|pgrls --out DIR [--rules PATH]
The folder holds answer_key.json and the app folders, as planted/ does. --rules is the semgrep-rules clone
(docs/baselines.md 2.1), needed for semgrep only. Commands are those of docs/baselines.md section 2.
Saves DIR/raw/<app>__<side>.<json|csv> and DIR/<app>__<side>.json. Run one at a time: it uses Docker.
"""
import argparse
import json
import os
import subprocess  # noqa: S404 - fixed argument lists, no shell
import sys
from pathlib import Path

from access_review.adapters import ADAPTERS
from access_review.adapters._common import unreadable
from access_review.scoring import expected_runs

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "acr-baselines:m52"
EXT = {"semgrep": "json", "pgrls": "json", "rlsautotest": "json", "advisors": "csv"}
# pgrls exits 1 when it reports violations; the others exit 0 on a normal run.
OK_EXIT = {"semgrep": (0,), "pgrls": (0, 1), "rlsautotest": (0,), "advisors": (0,)}


def _docker(folder, rules=None):
    mounts = ["-v", f"{folder}:/work/planted:ro"] + (["-v", f"{rules}:/rules:ro"] if rules else [])
    return ["docker", "run", "--rm", "--network", "none", *mounts, "-w", "/work", IMAGE]


def command(tool, folder, migrations, rules=None):
    """The argument list for one run, or a string saying why this folder cannot be run."""
    folder, relative = Path(folder).resolve(), Path(migrations).resolve().relative_to(Path(folder).resolve())
    if tool == "semgrep":
        if not rules:
            return "semgrep needs --rules"
        return [*_docker(folder, Path(rules).resolve()), "semgrep", "scan", "--config", "/rules/generic",
                "--metrics", "off", "--disable-version-check", "--json", "--quiet", f"planted/{relative.as_posix()}"]
    if tool == "pgrls":
        files = sorted(Path(migrations).glob("*.sql"))  # the sandbox's order; pgrls joins repeated --sql-file in order
        if not files:
            return "pgrls: no .sql file in the migrations folder"
        sql = [arg for f in files for arg in ("--sql-file", f"planted/{(relative / f.name).as_posix()}")]
        return [*_docker(folder), "pgrls", "lint", *sql, "--format", "json"]
    script = {"advisors": "advisors/run_splinter.py", "rlsautotest": "rlsautotest/run_rlsautotest.py"}[tool]
    return [sys.executable, str(ROOT / "baselines" / script), str(migrations)]


def run_command(argv):
    """(exit code, stdout, first stderr line)."""
    done = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",  # noqa: S603
                          env={**os.environ, "MSYS_NO_PATHCONV": "1"}, check=False)
    return done.returncode, done.stdout, (done.stderr.strip().splitlines() or [""])[0]


def run_one(tool, app, side, folder, migrations, rules, runner):
    """(raw text or None, run object). A failed command is not_checkable, never an empty result."""
    argv = command(tool, folder, migrations, rules)
    if isinstance(argv, str):
        return None, unreadable(app, side, f"{tool}: {argv}")
    try:
        code, out, err = runner(argv)
    except OSError as error:
        return None, unreadable(app, side, f"{tool}: could not start the command ({error})")
    if code not in OK_EXIT[tool]:
        return out, unreadable(app, side, f"{tool}: exit code {code}. {err}")
    return out, ADAPTERS[tool](out, app, side)


def main(argv, runner=run_command):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder")
    parser.add_argument("--tool", required=True, choices=sorted(ADAPTERS))
    parser.add_argument("--out", required=True)
    parser.add_argument("--rules")
    args = parser.parse_args(argv)
    out = Path(args.out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    for app, side, migrations in expected_runs(args.folder):
        raw, result = run_one(args.tool, app, side, args.folder, migrations, args.rules, runner)
        if raw is not None:
            (out / "raw" / f"{app}__{side}.{EXT[args.tool]}").write_text(raw, encoding="utf-8", newline="")
        text = json.dumps(result, indent=2, sort_keys=True) + chr(10)
        (out / f"{app}__{side}.json").write_text(text, encoding="utf-8")
        print(f"{app}/{side}: {len(result['findings'])} findings, not_checkable={result['not_checkable']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
