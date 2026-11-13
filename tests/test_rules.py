import pytest
from conftest import PLANTED

from access_review.evidence import Evidence
from access_review.probes import user_reads_rows, visitor_reads_rows
from access_review.rules import another_users_rows, owner_column
from access_review.sandbox import sandbox

USER_A = "11111111-1111-1111-1111-111111111111"


def _user_a_finding(app, variant):
    with sandbox(PLANTED / app / variant / "migrations", baseline=True) as box:
        owner = owner_column(box, "profiles")
        return owner, another_users_rows("profiles", owner, user_reads_rows(box, "profiles", USER_A))


@pytest.mark.parametrize("app", ["rows-01-profiles", "rows-02-profiles-all-authenticated"])
def test_vulnerable_apps_give_one_proved_finding(app):
    owner, finding = _user_a_finding(app, "vulnerable")
    assert owner == "owner_id"
    assert (finding.flaw_id, finding.status, finding.table) == ("R2", "proved", "profiles")
    assert finding.actor == f"user:{USER_A}"
    assert len(finding.proof[0].rows_seen) == 2  # the proof is what actually came back


@pytest.mark.parametrize("app", ["rows-01-profiles", "rows-02-profiles-all-authenticated"])
def test_fixed_twins_give_no_finding(app):
    # Negative control: the fixed twin shows user A only their own row.
    assert _user_a_finding(app, "fixed")[1] is None


def test_locked_out_app_gives_no_finding():
    assert _user_a_finding("rows-03-locked-out", "fixed")[1] is None


def test_public_table_without_owner_is_needs_decision_not_proved():
    with sandbox(PLANTED / "decoy-01-public-posts" / "migrations", baseline=True) as box:
        assert owner_column(box, "posts") is None
        finding = another_users_rows("posts", None, visitor_reads_rows(box, "posts"))
    assert (finding.flaw_id, finding.status) == ("R1", "needs_decision")
    assert "secure" not in (finding.explanation + finding.fix).lower()


def test_no_finding_when_the_read_was_refused_or_empty():
    refused = Evidence("visitor_reads_rows", "visitor", "SELECT 1", "permission_denied", [], "permission denied")
    empty = Evidence("visitor_reads_rows", "visitor", "SELECT 1", "ok", [])
    assert another_users_rows("posts", None, refused) is None
    assert another_users_rows("posts", None, empty) is None


def test_user_who_sees_only_their_own_rows_gets_no_finding():
    own = Evidence("user_reads_rows", f"user:{USER_A}", "SELECT 1", "ok", [{"owner_id": USER_A}])
    assert another_users_rows("profiles", "owner_id", own) is None
