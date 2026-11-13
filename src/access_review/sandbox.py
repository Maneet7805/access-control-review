"""Throwaway PostgreSQL in Docker, rebuilt from an app's migration files."""
import re
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
PIDS_LIMIT = "200"
MIGRATION_TIMEOUT_SECONDS = 30
# Linux capabilities the image needs to start. Everything else is dropped. Found by test.
START_CAPABILITIES = ("CHOWN", "DAC_OVERRIDE", "FOWNER", "SETGID", "SETUID")


# What psql prints when a migration fails, mapped to a plain-words reason. First match wins.
_REASONS = (
    ("missing_extension", re.compile(r'extension "([^"]+)" is not available'),
     'needs the extension "{0}", which the sandbox database does not have'),
    ("unknown_schema", re.compile(r'schema "([^"]+)" does not exist'),
     'refers to the schema "{0}", which does not exist in the rebuilt database'),
    ("syntax_error", re.compile(r'syntax error at or near "([^"]*)"'),
     'has a SQL syntax error near "{0}"'),
)
_ERROR_LINE = re.compile(r"psql:<stdin>:(\d+): ERROR:\s+(.*)")


class NotCheckable(subprocess.CalledProcessError):
    """A migration could not be applied, so the app cannot be reviewed.

    `line` is the line where the failing statement ends, which is where psql reports it.
    """

    def __init__(self, returncode, cmd, stderr, file, line, kind, reason):
        super().__init__(returncode, cmd, stderr=stderr)
        self.file, self.line, self.kind, self.reason = file, line, kind, reason

    def __str__(self):
        return f"{self.file}, line {self.line}: this app {self.reason}"


def _explain(error, sql_file):
    """Turn a failed psql run into NotCheckable. Unknown errors keep psql's own first line."""
    stderr = error.stderr or ""
    found = _ERROR_LINE.search(stderr)
    line, message = (int(found.group(1)), found.group(2)) if found else (0, stderr.strip().splitlines()[0:1] or [""])[0]
    for kind, pattern, template in _REASONS:
        match = pattern.search(message)
        if match:
            return NotCheckable(error.returncode, error.cmd, stderr, sql_file.name, line, kind,
                                template.format(*match.groups()))
    return NotCheckable(error.returncode, error.cmd, stderr, sql_file.name, line, "other",
                        f"could not be applied: {message}")


def _docker(*args, stdin=None, timeout=DOCKER_TIMEOUT_SECONDS):
    return subprocess.run(
        ["docker", *args], input=stdin, capture_output=True, text=True, check=True, timeout=timeout,
    ).stdout.strip()


class Sandbox:
    """A running sandbox database. It has no network, so SQL goes in through `docker exec psql`."""

    def __init__(self, name):
        self.name = name

    def run(self, sql, user="postgres"):
        """Run `sql` as `user`, return what psql prints (one line per row, columns joined by |)."""
        return _docker("exec", "-i", self.name, "psql", "-h", "127.0.0.1", "-U", user, "-X", "-q", "-At",
                       "-v", "ON_ERROR_STOP=1", "-f", "-", stdin=sql)


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


@contextmanager
def sandbox(migrations_dir, baseline=False):
    """Start a fresh database, apply every .sql file in order, yield a Sandbox to run SQL in.

    The container has no network, no Linux capabilities beyond START_CAPABILITIES, no new privileges, and
    limits on memory, CPU and processes. A migration that runs longer than MIGRATION_TIMEOUT_SECONDS is killed.

    With baseline=True the database is Supabase's image plus baseline.sql, and migrations run as the
    non-superuser postgres role, as on a hosted project. The default stays plain postgres:16 until the
    planted apps are rewritten.
    """
    name = f"{LABEL}-{uuid.uuid4().hex[:8]}"
    password = secrets.token_hex(16)
    try:
        _docker("run", "-d", "--rm", "--name", name, "--label", LABEL,
                "--network", "none", "--cap-drop", "ALL",
                *[arg for cap in START_CAPABILITIES for arg in ("--cap-add", cap)],
                "--security-opt", "no-new-privileges", "--pids-limit", PIDS_LIMIT,
                "--memory", MEMORY_LIMIT, "--memory-swap", MEMORY_LIMIT, "--cpus", CPU_LIMIT,
                "-e", f"POSTGRES_PASSWORD={password}",
                SUPABASE_IMAGE if baseline else IMAGE)
        _wait_until_ready(name)
        if baseline:
            _docker("exec", "-i", name, "psql", "-h", "127.0.0.1", "-U", "supabase_admin",
                    "-d", "postgres", "-v", "ON_ERROR_STOP=1", stdin=BASELINE.read_text())
        for sql_file in sorted(Path(migrations_dir).glob("*.sql")):
            try:
                _docker("exec", "-i", name, "psql", "-h", "127.0.0.1", "-U", "postgres",
                        "-v", "ON_ERROR_STOP=1", "-f", "-", stdin=sql_file.read_text(),
                        timeout=MIGRATION_TIMEOUT_SECONDS)
            except subprocess.CalledProcessError as error:
                raise _explain(error, sql_file) from error
            except subprocess.TimeoutExpired as error:
                raise NotCheckable(-1, error.cmd, "", sql_file.name, 0, "timeout",
                                   f"ran longer than {MIGRATION_TIMEOUT_SECONDS} seconds and was stopped") from error
        yield Sandbox(name)
    finally:
        _remove(name)
