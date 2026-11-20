"""Command line: python -m fix_check recheck <app> <fix.sql> [--key answer_key.json]

<app> is an app folder that holds vulnerable/migrations (for example planted/rows-01-profiles).
Exit code 0: fix works. 1: fix does not work. 2: the check cannot run.
"""
import argparse
import json
import sys
from pathlib import Path

from fix_check.recheck import CannotRun, format_run, recheck


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m fix_check")
    commands = parser.add_subparsers(dest="command", required=True)
    parser_recheck = commands.add_parser("recheck", help="add a fix to a copy of the vulnerable app and test it")
    parser_recheck.add_argument("app")
    parser_recheck.add_argument("fix")
    parser_recheck.add_argument("--key", help="answer key file (default: answer_key.json next to the app folder)")
    args = parser.parse_args(argv)
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
