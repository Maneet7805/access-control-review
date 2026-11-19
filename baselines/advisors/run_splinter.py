"""Run the pinned splinter.sql (Supabase advisor lints) on one folder of migrations; print the rows as CSV.

The database is the sandbox's (no network). The lints are read-only catalog queries: they are not attacks.

Usage: python baselines/advisors/run_splinter.py <migrations folder>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from access_review.sandbox import _docker, sandbox  # noqa: E402

LINTS = Path(__file__).with_name("splinter.sql")


def main(migrations):
    with sandbox(migrations, baseline=True) as box:
        out = _docker("exec", "-i", box.name, "psql", "-h", "127.0.0.1", "-U", "postgres", "-X", "-q", "--csv",
                      "-v", "ON_ERROR_STOP=1", "-f", "-", stdin=LINTS.read_text(encoding="utf8"))
    sys.stdout.buffer.write(out.encode() + b"\n")


if __name__ == "__main__":
    main(sys.argv[1])
