"""Run the tool on every scored folder of planted/ and save the raw findings JSON, one file per run.

Usage: python scripts/run_devset.py planted/ [--out results/devset] [--only app/side]
Score the saved files with: python -m access_review.scoring planted/ [--runs DIR]
Run one at a time: each run starts a Docker container.
"""
import json
import sys
from pathlib import Path

from access_review.cli import NOTE_NOT_RUN, review
from access_review.sandbox import NotCheckable, sandbox
from access_review.scoring import expected_runs


def run_folder(app, side, migrations):
    """One run as the scorer reads it. A probe error is a note that tests could not run."""
    try:
        with sandbox(migrations, baseline=True) as box:
            findings, notes = review(box)
    except NotCheckable as error:
        return {"app": app, "side": side, "not_checkable": True, "probe_errors": False,
                "findings": [], "notes": [str(error)]}
    return {"app": app, "side": side, "not_checkable": False,
            "probe_errors": any(n.startswith(NOTE_NOT_RUN.split("{}")[0]) for n in notes),
            "findings": [f.to_dict() for f in findings], "notes": notes}


def main(argv):
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else Path("results/devset")
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    out.mkdir(parents=True, exist_ok=True)
    for app, side, migrations in expected_runs(argv[0]):
        if only and only != f"{app}/{side}":
            continue
        result = run_folder(app, side, migrations)
        text = json.dumps(result, indent=2, sort_keys=True) + chr(10)
        (out / f"{app}__{side}.json").write_text(text, encoding="utf-8")
        print(f"{app}/{side}: {len(result['findings'])} findings, not_checkable={result['not_checkable']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
