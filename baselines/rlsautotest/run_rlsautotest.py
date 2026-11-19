"""Run rlsautotest on one planted folder and print its JSON report.

The database is the same Supabase image the sandbox uses, started with the sandbox's limits and no published
port, on a Docker network created with --internal, so it cannot reach or be reached from the internet or the host.
The tool runs in the pinned image on that same network. Everything is removed at the end.

Usage: python baselines/rlsautotest/run_rlsautotest.py <migrations folder>
"""
import secrets
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from access_review.sandbox import (  # noqa: E402
    BASELINE,
    CPU_LIMIT,
    MEMORY_LIMIT,
    PIDS_LIMIT,
    START_CAPABILITIES,
    SUPABASE_IMAGE,
    _docker,
    _wait_until_ready,
)

TOOL_IMAGE = "acr-baselines:m52"
LABEL = "acr-baseline-rlsautotest"


def main(migrations):
    tag = uuid.uuid4().hex[:8]
    net, db, password = f"acr-rls-net-{tag}", f"acr-rls-db-{tag}", secrets.token_hex(16)
    try:
        _docker("network", "create", "--internal", "--label", LABEL, net)
        _docker("run", "-d", "--rm", "--name", db, "--label", LABEL, "--network", net, "--network-alias", "db",
                "--cap-drop", "ALL", *[a for c in START_CAPABILITIES for a in ("--cap-add", c)],
                "--security-opt", "no-new-privileges", "--pids-limit", PIDS_LIMIT,
                "--memory", MEMORY_LIMIT, "--memory-swap", MEMORY_LIMIT, "--cpus", CPU_LIMIT,
                "-e", f"POSTGRES_PASSWORD={password}", SUPABASE_IMAGE)
        _wait_until_ready(db)
        _docker("exec", "-i", db, "psql", "-h", "127.0.0.1", "-U", "supabase_admin", "-d", "postgres",
                "-v", "ON_ERROR_STOP=1", stdin=BASELINE.read_text())
        for sql in sorted(Path(migrations).glob("*.sql")):
            _docker("exec", "-i", db, "psql", "-h", "127.0.0.1", "-U", "postgres", "-v", "ON_ERROR_STOP=1",
                    "-f", "-", stdin=sql.read_text())
        # postgres is the role the migrations ran as; the tool needs no rights beyond it (see ASSUMPTIONS.md).
        # The tool prints its text report and the JSON to the same stream, so the JSON goes to a file and is read back.
        out = _docker("run", "--rm", "--network", net, TOOL_IMAGE, "sh", "-c",
                      f"rlsautotest --db-url postgresql://postgres:{password}@db:5432/postgres --schema public "
                      "--report --report-json /tmp/r.json --no-fail --quiet >/dev/null 2>&1; cat /tmp/r.json")
        sys.stdout.buffer.write(out.encode() + b"\n")
    finally:
        subprocess.run(["docker", "rm", "-fv", db], capture_output=True)
        subprocess.run(["docker", "network", "rm", net], capture_output=True)


if __name__ == "__main__":
    main(sys.argv[1])
