import json

import pytest

from access_review.probes import visitor_reads_rows
from access_review.sandbox import sandbox
from conftest import PLANTED

ANSWER_KEY = json.loads((PLANTED / "answer_key.json").read_text())


@pytest.mark.parametrize("variant", ["vulnerable", "fixed"])
def test_visitor_row_read_matches_answer_key(variant):
    planted_flaws = ANSWER_KEY["rows-01-profiles"][variant]
    expect_leak = any(f["kind"] == "rows" and f["actor"] == "visitor" for f in planted_flaws)
    with sandbox(PLANTED / "rows-01-profiles" / variant / "migrations") as conn_str:
        rows = visitor_reads_rows(conn_str, "profiles")
    assert bool(rows) == expect_leak
