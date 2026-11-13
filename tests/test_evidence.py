import pytest
from conftest import PLANTED

from access_review.evidence import Evidence
from access_review.probes import user_reads_rows, visitor_reads_rows
from access_review.sandbox import sandbox

USER_A = "11111111-1111-1111-1111-111111111111"


@pytest.fixture(scope="module")
def vulnerable():
    with sandbox(PLANTED / "rows-01-profiles" / "vulnerable" / "migrations", baseline=True) as box:
        yield box


def test_evidence_survives_a_round_trip_through_json():
    original = Evidence("visitor_reads_rows", "visitor", 'SELECT * FROM "t"', "ok", [{"id": 1, "name": "é"}])
    assert Evidence.from_json(original.to_json()) == original


def test_evidence_with_an_unknown_result_is_rejected():
    with pytest.raises(ValueError):
        Evidence("p", "visitor", "SELECT 1", "probably_fine")


def test_visitor_probe_returns_evidence_of_the_rows_it_saw(vulnerable):
    evidence = visitor_reads_rows(vulnerable, "profiles")
    assert (evidence.probe, evidence.actor, evidence.result) == ("visitor_reads_rows", "visitor", "ok")
    assert evidence.statement == 'SELECT * FROM "profiles"'
    assert len(evidence.rows_seen) == 2 and evidence.error is None


def test_user_probe_names_the_user_in_its_evidence(vulnerable):
    evidence = user_reads_rows(vulnerable, "profiles", USER_A)
    assert (evidence.probe, evidence.actor, evidence.result) == ("user_reads_rows", f"user:{USER_A}", "ok")
    assert Evidence.from_json(evidence.to_json()) == evidence


def test_a_refused_read_is_recorded_as_permission_denied(tmp_path):
    # Negative control: no grant for anon, so the evidence shows a refusal and no rows.
    (tmp_path / "001.sql").write_text(
        "create table public.private_notes (id int); revoke all on public.private_notes from anon;")
    with sandbox(tmp_path, baseline=True) as box:
        evidence = visitor_reads_rows(box, "private_notes")
    assert (evidence.result, evidence.rows_seen) == ("permission_denied", [])
    assert "permission denied" in evidence.error


def test_a_missing_table_is_an_error_not_a_refusal(vulnerable):
    evidence = visitor_reads_rows(vulnerable, "no_such_table")
    assert evidence.result == "error" and "does not exist" in evidence.error
