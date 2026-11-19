"""Semgrep adapter. docs/baselines.md 3.2: no rule is mapped, so every item is unmapped."""
import json

from access_review.adapters._common import Mapped, unreadable


def adapt(text, app, side):
    try:
        data = json.loads(text)
        results, errors, scanned = data["results"], data["errors"], data["paths"]["scanned"]
        if not all(isinstance(part, list) for part in (results, errors, scanned)):
            raise TypeError("results, errors and paths.scanned must be lists")
    except (ValueError, KeyError, TypeError) as error:
        return unreadable(app, side, f"semgrep: output not readable ({error.__class__.__name__}: {error})")
    if errors:
        return unreadable(app, side, f"semgrep: the scan reported {len(errors)} error(s); a partial scan is no result")
    if not scanned:
        return unreadable(app, side, "semgrep: no file was scanned")
    mapped = Mapped("semgrep")
    mapped.skip(len(results))
    return mapped.run(app, side)
