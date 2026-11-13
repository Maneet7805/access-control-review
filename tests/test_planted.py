import json
import re

import pytest
from conftest import PLANTED

from access_review.probes import user_reads_rows, visitor_reads_rows
from access_review.sandbox import sandbox

ANSWER_KEY = json.loads((PLANTED / "answer_key.json").read_text())
VARIANTS = [
    (app, variant)
    for app in ANSWER_KEY
    for variant in ("vulnerable", "fixed")
    if (PLANTED / app / variant / "migrations").is_dir()
]
FIXED_TWINS = [(app, variant) for app, variant in VARIANTS if variant == "fixed"]
USER_A = "11111111-1111-1111-1111-111111111111"  # seeded as user-a in every planted app


def _planted(app, variant, flaw_id):
    return any(f["flaw_id"] == flaw_id for f in ANSWER_KEY[app][f"flaws_{variant}"])


@pytest.mark.parametrize("app,variant", VARIANTS)
def test_probes_match_answer_key(app, variant):
    with sandbox(PLANTED / app / variant / "migrations", baseline=True) as box:
        visitor_rows = visitor_reads_rows(box, "profiles").rows_seen
        user_a_rows = user_reads_rows(box, "profiles", USER_A).rows_seen
    assert bool(visitor_rows) == _planted(app, variant, "R1")
    user_a_sees_others = any(str(row["owner_id"]) != USER_A for row in user_a_rows)
    assert user_a_sees_others == _planted(app, variant, "R2")


@pytest.mark.parametrize("app,variant", VARIANTS)
def test_planted_migrations_do_not_create_roles(app, variant):
    # Supabase already has anon and authenticated; an app that creates them is not written the way real ones are.
    for sql_file in (PLANTED / app / variant / "migrations").glob("*.sql"):
        assert not re.search(r"create\s+role", sql_file.read_text(), re.IGNORECASE)


@pytest.mark.parametrize("app,variant", FIXED_TWINS)
def test_allowed_access_survives_in_the_fixed_twin(app, variant):
    with sandbox(PLANTED / app / variant / "migrations", baseline=True) as box:
        user_a_rows = user_reads_rows(box, "profiles", USER_A).rows_seen
    for allowed in ANSWER_KEY[app]["allowed"]:
        assert allowed["expect"] == "own_row_only"
        works = [str(row["owner_id"]) for row in user_a_rows] == [USER_A]
        # Negative control: an app marked locks_out_owner must fail this check.
        assert works == (allowed.get("expected_failure") is None)
