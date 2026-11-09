"""Throwaway PostgreSQL in Docker, rebuilt from an app's migration files."""
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

IMAGE = "postgres:16"
LABEL = "access-review-sandbox"
PASSWORD = "sandbox"
READY_TIMEOUT_SECONDS = 60


def _docker(*args, stdin=None):
    return subprocess.run(
        ["docker", *args], input=stdin, capture_output=True, text=True, check=True
    ).stdout.strip()


def _wait_until_ready(name):
    deadline = time.time() + READY_TIMEOUT_SECONDS
    while time.time() < deadline:
        # The image restarts Postgres once after init, so check a real query over TCP.
        probe = subprocess.run(
            ["docker", "exec", name, "psql", "-h", "127.0.0.1", "-U", "postgres", "-c", "SELECT 1"],
            capture_output=True,
        )
        if probe.returncode == 0:
            return
        time.sleep(1)
    raise TimeoutError(f"{name} not ready after {READY_TIMEOUT_SECONDS}s")


@contextmanager
def sandbox(migrations_dir):
    """Start a fresh database, apply every .sql file in order, yield its connection string."""
    name = f"{LABEL}-{uuid.uuid4().hex[:8]}"
    _docker("run", "-d", "--rm", "--name", name, "--label", LABEL,
            "-e", f"POSTGRES_PASSWORD={PASSWORD}", "-p", "127.0.0.1::5432", IMAGE)
    try:
        _wait_until_ready(name)
        for sql_file in sorted(Path(migrations_dir).glob("*.sql")):
            _docker("exec", "-i", name, "psql", "-h", "127.0.0.1", "-U", "postgres",
                    "-v", "ON_ERROR_STOP=1", stdin=sql_file.read_text())
        port = _docker("port", name, "5432/tcp").splitlines()[0].rsplit(":", 1)[1]
        yield f"postgresql://postgres:{PASSWORD}@127.0.0.1:{port}/postgres"
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
