import pytest
from conftest import ROOT

from access_review.sandbox import NotCheckable, sandbox

BROKEN = ROOT / "tests" / "fixtures" / "broken"


@pytest.mark.parametrize("folder,kind,reason", [
    ("missing_extension", "missing_extension",
     'needs the extension "no_such_extension", which the sandbox database does not have'),
    ("unknown_schema", "unknown_schema",
     'refers to the schema "nowhere", which does not exist in the rebuilt database'),
    ("syntax_error", "syntax_error", 'has a SQL syntax error near "selct"'),
])
def test_broken_migration_gives_its_own_reason_and_line(folder, kind, reason):
    with pytest.raises(NotCheckable) as caught, sandbox(BROKEN / folder):
        pass
    error = caught.value
    assert (error.kind, error.reason, error.file, error.line) == (kind, reason, "001.sql", 3)
    assert str(error) == f"001.sql, line 3: this app {reason}"


def test_good_migration_gives_no_reason(tmp_path):
    # Negative control: a fine app rebuilds and raises nothing.
    (tmp_path / "001.sql").write_text("-- app migration\ncreate table t (id int);\n")
    with sandbox(tmp_path) as box:
        assert box.run("select count(*) from t") == "0"
