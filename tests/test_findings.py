import json
import re

import pytest
from conftest import ROOT
from jsonschema import Draft202012Validator, ValidationError

from access_review.evidence import Evidence
from access_review.findings import FLAWS, Finding

SCHEMA = json.loads((ROOT / "schemas" / "finding.schema.json").read_text())
EVIDENCE = Evidence("user_reads_rows", "user:1111", 'SELECT * FROM "profiles"', "ok", [{"id": 1}, {"id": 2}])


def _finding(**changes):
    fields = {"id": "R2-profiles", "flaw_id": "R2", "actor": "user:1111", "proof": [EVIDENCE],
              "explanation": "A signed-in user can read other users' rows.", "fix": "Add a policy.",
              "status": "proved", "table": "profiles"}
    return Finding(**{**fields, **changes})


def test_sample_findings_validate_against_the_schema():
    validator = Draft202012Validator(SCHEMA)
    validator.validate(_finding().to_dict())
    validator.validate(_finding(status="needs_decision", flaw_id="R1", actor="visitor").to_dict())
    validator.validate(_finding(table=None, function="delete_user", flaw_id="U2").to_dict())


def test_finding_survives_a_round_trip_through_json():
    assert Finding.from_json(_finding().to_json()) == _finding()


def test_finding_without_evidence_is_rejected_in_code_and_by_the_schema():
    # Negative control for "nothing is proved without evidence".
    with pytest.raises(ValueError, match="evidence"):
        _finding(proof=[])
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate({**_finding().to_dict(), "proof": []})


def test_status_other_than_proved_or_needs_decision_is_rejected():
    with pytest.raises(ValueError):
        _finding(status="probably")
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate({**_finding().to_dict(), "status": "probably"})


def test_unknown_flaw_and_missing_target_are_rejected():
    with pytest.raises(ValueError):
        _finding(flaw_id="Z9")
    with pytest.raises(ValueError):
        _finding(table=None)
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate({k: v for k, v in _finding().to_dict().items() if k != "table"})


def test_owasp_tags_follow_the_flaw_catalogue_in_the_roadmap():
    text = (ROOT / "docs" / "ROADMAP.md").read_text()
    table = text.split("## Appendix A")[1].split("## Appendix B")[0]
    rows = re.findall(r"^\| (\w\d) \| \w+ \| .*? \| (.*?) \|$", table, re.M)
    catalogue = {flaw: [tag.strip() for tag in tags.split(",")] for flaw, tags in rows}
    assert FLAWS == catalogue
    assert _finding().owasp == ["A01", "API1"]
