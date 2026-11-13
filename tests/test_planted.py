import json
import re

import pytest
from conftest import PLANTED

from access_review.probes import user_reads_rows, visitor_reads_rows
from access_review.sandbox import sandbox

ANSWER_KEY = json.loads((PLANTED / "answer_key.json").read_text())
VARIANTS = [(app, variant) for app in ANSWER_KEY for variant in ("vulnerable", "fixed")]
USER_A = "11111111-1111-1111-1111-111111111111"  # seeded as user-a in every planted app


def _planted(app, variant, flaw_id):
    return any(f["flaw_id"] == flaw_id for f in ANSWER_KEY[app][f"flaws_{variant}"])


@pytest.mark.parametrize("app,variant", VARIANTS)
def test_probes_match_answer_key(app, variant):
    with sandbox(PLANTED / app / variant / "migrations", baseline=True) as conn_str:
        visitor_rows = visitor_reads_rows(conn_str, "profiles")
        user_a_rows = user_reads_rows(conn_str, "profiles", USER_A)
    assert bool(visitor_rows) == _planted(app, variant, "R1")
    user_a_sees_others = any(str(row["owner_id"]) != USER_A for row in user_a_rows)
    assert user_a_sees_others == _planted(app, variant, "R2")


@pytest.mark.parametrize("app,variant", VARIANTS)
def test_planted_migrations_do_not_create_roles(app, variant):
    # Supabase already has anon and authenticated; an app that creates them is not written the way real ones are.
    for sql_file in (PLANTED / app / variant / "migrations").glob("*.sql"):
        assert not re.search(r"create\s+role", sql_file.read_text(), re.IGNORECASE)
