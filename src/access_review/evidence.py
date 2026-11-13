"""What a probe ran and what it saw. Findings are built from this, never from raw rows."""
import json
from dataclasses import asdict, dataclass, field

RESULTS = ("ok", "permission_denied", "error")


@dataclass(frozen=True)
class Evidence:
    probe: str          # which attack, e.g. "visitor_reads_rows"
    actor: str          # who ran it: "visitor" or "user:<uuid>"
    statement: str      # the SQL that ran
    result: str         # one of RESULTS
    rows_seen: list = field(default_factory=list)  # rows that came back, as dicts
    error: str | None = None  # the database's first error line, if any

    def __post_init__(self):
        if self.result not in RESULTS:
            raise ValueError(f"result must be one of {RESULTS}, not {self.result!r}")

    def to_json(self):
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, text):
        return cls(**json.loads(text))
