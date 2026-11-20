"""Build a fix attempt: a copy of a vulnerable app's migrations plus one fix file the sandbox applies last."""
import shutil
from pathlib import Path


class AttemptRefused(ValueError):
    """The fix cannot be added. The message is a plain reason."""


def _fix_text(fix_sql):
    if isinstance(fix_sql, Path):
        if not fix_sql.is_file():
            raise AttemptRefused("the fix must be a single file, and this path is not a file")
        fix_sql = fix_sql.read_bytes()
    if isinstance(fix_sql, (bytes, bytearray)):
        try:
            fix_sql = bytes(fix_sql).decode("utf-8")
        except UnicodeDecodeError:
            raise AttemptRefused("the fix is not text") from None
    if not isinstance(fix_sql, str):
        raise AttemptRefused("the fix must be one block of SQL text, in a single file")
    if "\0" in fix_sql:
        raise AttemptRefused("the fix is not text")
    if not fix_sql.strip():
        raise AttemptRefused("the fix is empty")
    return fix_sql


def build_attempt(vulnerable_migrations, fix_sql, workdir):
    """Copy the migrations to `workdir`, add `fix_sql` as one new .sql file that sorts last, return `workdir`.

    The sandbox applies `sorted(Path(dir).glob("*.sql"))`. The fix is named after the largest existing name,
    so it sorts after every original, and the real sort is checked on the copy before returning.
    """
    source, workdir = Path(vulnerable_migrations).resolve(), Path(workdir).resolve()
    text = _fix_text(fix_sql)
    if not source.is_dir():
        raise AttemptRefused("the vulnerable migrations folder does not exist")
    if workdir == source or source in workdir.parents or workdir in source.parents:
        raise AttemptRefused("the work folder must be outside the vulnerable app folder")
    if workdir.exists() and any(workdir.iterdir()):
        raise AttemptRefused("the work folder is not empty")
    shutil.copytree(source, workdir, dirs_exist_ok=True)
    names = [p.name for p in workdir.glob("*.sql")]
    # Largest under both a case-sensitive and a case-insensitive sort (Windows compares paths without case).
    top = max(names + [n.lower() for n in names], default="")
    fix = workdir / (top[:-4] + "_zz_fix.sql" if top else "zz_fix.sql")
    fix.write_bytes(text.encode("utf-8"))
    if sorted(workdir.glob("*.sql"))[-1] != fix:
        shutil.rmtree(workdir)
        raise AttemptRefused("the fix file would not be applied last")
    return workdir
