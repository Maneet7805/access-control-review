"""Command line: python -m fix_check recheck <app> <fix.sql> [--key answer_key.json]
              python -m fix_check run reference --out DIR [--fixes fixes/reference] [--planted planted]

<app> is an app folder that holds vulnerable/migrations (for example planted/rows-01-profiles).
Exit code 0: fix works. 1: fix does not work. 2: the check cannot run.
run: exit 0 when every attempt ran (failed fixes are results), 2 when any attempt could not run.
"""
import argparse
import json
import sys
from pathlib import Path

from fix_check.recheck import CannotRun, format_run, recheck
from fix_check.run import run_reference, totals


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m fix_check")
    commands = parser.add_subparsers(dest="command", required=True)
    parser_recheck = commands.add_parser("recheck", help="add a fix to a copy of the vulnerable app and test it")
    parser_recheck.add_argument("app")
    parser_recheck.add_argument("fix")
    parser_recheck.add_argument("--key", help="answer key file (default: answer_key.json next to the app folder)")
    parser_run = commands.add_parser("run", help="run every fix of one source and save one run object per attempt")
    parser_run.add_argument("source", choices=["reference"])
    parser_run.add_argument("--out", required=True)
    parser_run.add_argument("--fixes", default="fixes/reference")
    parser_run.add_argument("--planted", default="planted")
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            runs = run_reference(args.out, args.fixes, args.planted)
        except (OSError, ValueError, KeyError) as error:
            print(f"Cannot run: {error}", file=sys.stderr)
            return 2
        print(totals(runs))
        return 2 if any("cannot_run" in r for r in runs) else 0
    try:
        key = None
        if args.key:
            key = json.loads(Path(args.key).read_text(encoding="utf-8"))
        run = recheck(args.app, Path(args.fix), key)
    except (CannotRun, OSError, ValueError) as error:
        print(f"Cannot run: {error}", file=sys.stderr)
        return 2
    print(format_run(run))
    return 0 if run["works"] else 1


if __name__ == "__main__":
    sys.exit(main())
