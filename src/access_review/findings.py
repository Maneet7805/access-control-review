"""A finding: one proven (or undecided) access-control problem, in a fixed shape (schema version 0.1)."""
import json
from dataclasses import asdict, dataclass

from access_review.evidence import Evidence

SCHEMA_VERSION = "0.1"
STATUSES = ("proved", "needs_decision")
# Flaw ids and their OWASP tags, copied from Appendix A of docs/ROADMAP.md (a test keeps them in step).
FLAWS = {
    "R1": ["A01", "API1"], "R2": ["A01", "API1"], "R3": ["A01"], "R4": ["A01", "API1"],
    "R5": ["A01", "API1"], "R6": ["A01", "API1"], "R7": ["A01", "API1"],
    "C1": ["API3"], "C2": ["API3"], "V1": ["A01"],
    "U1": ["API5"], "U2": ["API5"], "U3": ["API5"],
}


@dataclass(frozen=True)
class Finding:
    id: str
    flaw_id: str
    actor: str
    proof: list  # list of Evidence; never empty
    explanation: str
    fix: str
    status: str
    table: str | None = None
    column: str | None = None
    function: str | None = None

    def __post_init__(self):
        if self.flaw_id not in FLAWS:
            raise ValueError(f"unknown flaw id {self.flaw_id!r}")
        if self.status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}, not {self.status!r}")
        if not self.proof:
            raise ValueError("a finding needs evidence")
        if not (self.table or self.column or self.function):
            raise ValueError("a finding must name a table, column or function")

    @property
    def owasp(self):
        return FLAWS[self.flaw_id]

    def to_dict(self):
        data = {"schema_version": SCHEMA_VERSION, "owasp": self.owasp, **asdict(self)}
        return {key: value for key, value in data.items() if value is not None}

    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text):
        data = json.loads(text)
        if data.pop("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported schema version")
        data.pop("owasp")
        return cls(**{**data, "proof": [Evidence(**item) for item in data["proof"]]})
