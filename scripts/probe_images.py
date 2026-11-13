"""Start each candidate base image and print what it provides for a Supabase-like sandbox.

Usage: python scripts/probe_images.py
Prints one table per image. Containers are throwaway, have no published ports and are removed at the end.
"""

import subprocess
import sys
import time

IMAGES = ["postgres:16", "supabase/postgres:15.19.0.019"]
LABEL = "access-review-image-spike"
PASSWORD = "spike-only"  # noqa: S105 - throwaway container, no published port

QUERIES = {
    "version": "select version()",
    "roles": (
        "select rolname, rolsuper, rolbypassrls, rolcanlogin, rolinherit from pg_roles "
        "where rolname in ('postgres','anon','authenticated','service_role','authenticator','supabase_admin') "
        "order by 1"
    ),
    "schemas": (
        "select nspname from pg_namespace where nspname in "
        "('auth','storage','extensions','graphql','graphql_public','realtime','vault') order by 1"
    ),
    "every function in schema auth": (
        r"select n.nspname||'.'||p.proname, left(regexp_replace(p.prosrc, '\s+', ' ', 'g'), 110) "
        "from pg_proc p join pg_namespace n on n.oid = p.pronamespace "
        "where n.nspname = 'auth' order by 1"
    ),
    "auth.users columns": (
        "select count(*) from information_schema.columns where table_schema = 'auth' and table_name = 'users'"
    ),
    "extensions": "select extname from pg_extension order by 1",
    "default privileges (public)": (
        "select pg_get_userbyid(d.defaclrole), d.defaclobjtype, d.defaclacl::text from pg_default_acl d "
        "where d.defaclnamespace in (0, 'public'::regnamespace) order by 1, 2"
    ),
}


def sh(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:4])} failed: {result.stderr.strip()[-300:]}")
    return result.stdout.strip()


def query(container: str, user: str, sql: str) -> str:
    return sh("docker", "exec", container, "psql", "-U", user, "-d", "postgres", "-At", "-F", " | ", "-c", sql)


def wait_ready(container: str, timeout: int = 120) -> str:
    """Return a role that can log in over TCP after three good answers in a row, or raise.

    The images start a temporary server on the unix socket only during setup, so a TCP answer means the final
    server is up. The role may not be a superuser.
    """
    deadline, good = time.time() + timeout, 0
    while time.time() < deadline:
        for user in ("postgres", "supabase_admin"):
            if sh("docker", "exec", "-e", f"PGPASSWORD={PASSWORD}", container, "psql", "-h", "127.0.0.1", "-U", user,
                  "-d", "postgres", "-Atc", "select 1", check=False):
                good += 1
                if good >= 3:
                    return user
                break
        else:
            good = 0
        time.sleep(1.5)
    raise RuntimeError(f"{container} was not ready in {timeout}s")


def probe(image: str) -> None:
    print(f"\n===== {image} =====")
    name = sh("docker", "run", "-d", "--rm", "--label", LABEL, "-e", f"POSTGRES_PASSWORD={PASSWORD}", image)
    try:
        user = wait_ready(name)
        time.sleep(3)  # let startup memory settle
        print(f"connected as: {user}")
        for title, sql in QUERIES.items():
            print(f"\n[{title}]")
            print(query(name, user, sql) or "(none)")
        print("\n[idle memory]")
        print(sh("docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", name))
    finally:
        sh("docker", "rm", "-f", name, check=False)


def main() -> int:
    for image in IMAGES:
        try:
            probe(image)
        except RuntimeError as error:
            print(f"FAILED {image}: {error}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
