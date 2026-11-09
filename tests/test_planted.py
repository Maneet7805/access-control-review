import json

import pytest

from access_review.probes import user_reads_rows, visitor_reads_rows
from access_review.sandbox import sandbox
from conftest import PLANTED

ANSWER_KEY = json.loads((PLANTED / "answer_key.json").read_text())
VARIANTS = [(app, variant) for app in ANSWER_KEY for variant in ("vulnerable", "fixed")]


def _is_planted(app, variant, actor):
    return any(f["kind"] == "rows" and f["actor"] == actor for f in ANSWER_KEY[app][variant])


@pytest.mark.parametrize("app,variant", VARIANTS)
def test_probes_match_answer_key(app, variant):
    with sandbox(PLANTED / app / variant / "migrations") as conn_str:
        visitor_rows = visitor_reads_rows(conn_str, "profiles")
        user_a_rows = user_reads_rows(conn_str, "profiles", "user-a")
    assert bool(visitor_rows) == _is_planted(app, variant, "visitor")
    user_a_sees_others = any(row["owner_id"] != "user-a" for row in user_a_rows)
    assert user_a_sees_others == _is_planted(app, variant, "user-a")
