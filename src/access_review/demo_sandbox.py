"""Show how many rows a visitor, user A and user B can read in a rebuilt app.

Usage: python -m access_review.demo_sandbox <migrations folder> [table]
"""
import sys

from access_review.probes import user_reads_rows, visitor_reads_rows
from access_review.sandbox import NotCheckable, sandbox

# The two users every planted app seeds.
USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(__doc__.strip())
        return 2
    migrations, table = args[0], (args[1] if len(args) > 1 else "profiles")
    try:
        with sandbox(migrations, baseline=True) as box:
            counts = [("visitor", len(visitor_reads_rows(box, table))),
                      ("user A", len(user_reads_rows(box, table, USER_A))),
                      ("user B", len(user_reads_rows(box, table, USER_B)))]
    except NotCheckable as error:
        print(f"Not checkable: {error}")
        return 1
    print(f"Rows each person can read in table {table}:")
    for who, count in counts:
        print(f"  {who:<8} {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
