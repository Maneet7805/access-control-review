"""Throwaway PostgreSQL in Docker, rebuilt from an app's migration files."""
import secrets
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

IMAGE = "postgres:16"
SUPABASE_IMAGE = "supabase/postgres:15.19.0.019"
BASELINE = Path(__file__).with_name("baseline.sql")
LABEL = "access-review-sandbox"
READY_TIMEOUT_SECONDS = 60
DOCKER_TIMEOUT_SECONDS = 120
MEMORY_LIMIT = "512m"
CPU_LIMIT = "1"


def _docker(*args, stdin=None):
    return subprocess.run(
        ["docker", *args], input=stdin, capture_output=True, text=True, check=True,
        timeout=DOCKER_TIMEOUT_SECONDS,
    ).stdout.strip()


def _wait_until_ready(name):
    deadline = time.time() + READY_TIMEOUT_SECONDS
    while time.time() < deadline:
        # The image restarts Postgres once after init, so check a real query over TCP.
        probe = subprocess.run(
            ["docker", "exec", name, "psql", "-h", "127.0.0.1", "-U", "postgres", "-c", "SELECT 1"],
            capture_output=True, timeout=DOCKER_TIMEOUT_SECONDS,
        )
        if probe.returncode == 0:
            return
        time.sleep(1)
    raise TimeoutError(f"{name} not ready after {READY_TIMEOUT_SECONDS}s")


def _remove(name):
    result = subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True,
                            timeout=DOCKER_TIMEOUT_SECONDS)
    # "No such container" is fine: docker run may have failed before creating it.
    if result.returncode != 0 and "No such container" not in result.stderr:
        raise RuntimeError(f"could not remove {name}: {result.stderr.strip()}")


# TODO(Maneet, 09 Nov 2026): migrations run as superuser with network access; isolate before reviewing untrusted repos.
@contextmanager
def sandbox(migrations_dir, baseline=False):
    """Start a fresh database, apply every .sql file in order, yield its connection string.

    With baseline=True the database is Supabase's image plus baseline.sql, and migrations run as the
    non-superuser postgres role, as on a hosted project. The default stays plain postgres:16 until the
    planted apps are rewritten.
    """
    name = f"{LABEL}-{uuid.uuid4().hex[:8]}"
    password = secrets.token_hex(16)
    try:
        _docker("run", "-d", "--rm", "--name", name, "--label", LABEL,
                "--memory", MEMORY_LIMIT, "--cpus", CPU_LIMIT,
                "-e", f"POSTGRES_PASSWORD={password}", "-p", "127.0.0.1::5432",
                SUPABASE_IMAGE if baseline else IMAGE)
        _wait_until_ready(name)
        if baseline:
            _docker("exec", "-i", name, "psql", "-h", "127.0.0.1", "-U", "supabase_admin",
                    "-d", "postgres", "-v", "ON_ERROR_STOP=1", stdin=BASELINE.read_text())
        for sql_file in sorted(Path(migrations_dir).glob("*.sql")):
            _docker("exec", "-i", name, "psql", "-h", "127.0.0.1", "-U", "postgres",
                    "-v", "ON_ERROR_STOP=1", stdin=sql_file.read_text())
        port = _docker("port", name, "5432/tcp").splitlines()[0].rsplit(":", 1)[1]
        yield f"postgresql://postgres:{password}@127.0.0.1:{port}/postgres"
    finally:
        _remove(name)
