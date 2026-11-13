"""Run the four checks CI runs and print PASS or FAIL for each. Exit code 0 only if all pass."""

import subprocess
import sys

CHECKS = {
    "ruff": ["-m", "ruff", "check", "."],
    "pytest": ["-m", "pytest", "-v"],
    "bandit": ["-m", "bandit", "-r", "src", "-ll"],
    "pip-audit": ["-m", "pip_audit", "--skip-editable"],
}


def run(name: str, command: list[str]) -> bool:
    """Run one command, print PASS or FAIL, and show the last lines of output if it failed."""
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = result.returncode == 0
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print("\n".join((result.stdout + result.stderr).strip().splitlines()[-15:]))
    return ok


def main() -> int:
    results = [run(name, [sys.executable, *args]) for name, args in CHECKS.items()]
    print("ALL PASS" if all(results) else "FAIL")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
