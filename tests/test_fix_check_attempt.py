import hashlib

import pytest
from conftest import PLANTED

from access_review.sandbox import sandbox
from fix_check.attempt import AttemptRefused, build_attempt

VULNERABLE = PLANTED / "rows-01-profiles" / "vulnerable" / "migrations"
FIX = "ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;\n"


def _hash(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob("*")) if p.is_file()}


def _originals(tmp_path, *names):
    src = tmp_path / "src"
    src.mkdir()
    for name in names:
        (src / name).write_text(f"-- {name}\n")
    return src


def test_copy_holds_originals_plus_one_new_file_that_sorts_last(tmp_path):
    out = build_attempt(VULNERABLE, FIX, tmp_path / "work")
    new = {p.name for p in out.iterdir()} - {p.name for p in VULNERABLE.iterdir()}
    assert len(new) == 1
    for original in VULNERABLE.iterdir():
        assert (out / original.name).read_bytes() == original.read_bytes()
    assert sorted(out.glob("*.sql"))[-1].name == new.pop()
    assert (sorted(out.glob("*.sql"))[-1]).read_text() == FIX


def test_original_folder_is_unchanged(tmp_path):
    before = _hash(VULNERABLE)
    build_attempt(VULNERABLE, FIX, tmp_path / "work")
    assert _hash(VULNERABLE) == before


@pytest.mark.parametrize("fix", ["", "  \n\t", b"", b"\xff\xfe\x00bad", "SELECT 1;\0", None, ["a.sql", "b.sql"]])
def test_empty_or_unusable_fix_is_refused(tmp_path, fix):
    with pytest.raises(AttemptRefused):
        build_attempt(VULNERABLE, fix, tmp_path / "work")
    assert not (tmp_path / "work").exists()


def test_fix_that_is_a_folder_is_refused(tmp_path):
    with pytest.raises(AttemptRefused, match="single file"):
        build_attempt(VULNERABLE, tmp_path, tmp_path / "work")


def test_fix_sorts_last_even_when_originals_have_late_or_upper_case_names(tmp_path):
    # Negative control: a fixed name such as "000_fix.sql" or "fix.sql" would sort first or in the middle.
    src = _originals(tmp_path, "001_init.sql", "zzz_late.sql", "ZZZ_UPPER.sql", "~tilde.sql")
    out = build_attempt(src, FIX, tmp_path / "work")
    ordered = sorted(out.glob("*.sql"))
    assert ordered[-1].read_text() == FIX
    assert {p.name for p in ordered[:-1]} == {p.name for p in src.glob("*.sql")}


def test_work_folder_inside_the_original_is_refused(tmp_path):
    src = _originals(tmp_path, "001_init.sql")
    before = _hash(src)
    with pytest.raises(AttemptRefused, match="outside"):
        build_attempt(src, FIX, src / "work")
    assert _hash(src) == before


def test_non_empty_work_folder_is_refused(tmp_path):
    (tmp_path / "work").mkdir()
    (tmp_path / "work" / "keep.txt").write_text("x")
    with pytest.raises(AttemptRefused, match="not empty"):
        build_attempt(VULNERABLE, FIX, tmp_path / "work")


def test_sandbox_applies_the_fix_last():
    # The sandbox's own ordering rule is `sorted(Path(dir).glob("*.sql"))`; this guards that it is still so.
    import inspect
    assert 'sorted(Path(migrations_dir).glob("*.sql"))' in inspect.getsource(sandbox)
