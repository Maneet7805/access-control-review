"""Supabase advisors adapter (splinter lints as CSV). Rules: docs/baselines.md 3.3."""
import csv
import io
import json

from access_review.adapters._common import Mapped, clean, unreadable

TABLE_LINTS = {"rls_disabled_in_public": "R1", "policy_exists_rls_disabled": "R1",
               "security_definer_view": "V1", "materialized_view_in_api": "V1"}
SIGNED_OUT = {"anon", "public"}


def _always_true(meta):
    """Flaw ids of an always-true policy, by command and role list. Empty means unmapped."""
    command, roles = meta.get("command"), set(meta.get("roles") or [])
    if command == "INSERT" and roles & SIGNED_OUT:
        return ["R3"]
    if command == "INSERT" and roles:
        return ["R4"]
    if command == "UPDATE":
        fields = (("R5", "permissive_using"), ("R7", "permissive_with_check"))
        return [flaw for flaw, field in fields if meta.get(field)]
    if command == "DELETE" and meta.get("permissive_using"):
        return ["R6"]
    return []


def _items(lint, meta):
    """(flaw id, target) pairs for one lint row."""
    name = clean(meta.get("name") or "")
    if not name:
        return []
    if lint in TABLE_LINTS:
        return [(TABLE_LINTS[lint], {"table": name})]
    if lint == "rls_policy_always_true":
        return [(flaw, {"table": name}) for flaw in _always_true(meta)]
    if lint == "anon_security_definer_function_executable":
        return [("U3", {"function": name})]
    if lint == "authenticated_security_definer_function_executable":
        return [("U1", {"function": name})]
    if lint == "sensitive_columns_exposed":
        return [("C2", {"table": name, "column": clean(c)}) for c in meta.get("sensitive_columns") or []]
    return []


def _line(row):
    out = io.StringIO()
    csv.writer(out, lineterminator="").writerow(row.values())
    return out.getvalue()


def adapt(text, app, side):
    try:
        reader = csv.DictReader(io.StringIO(text))
        if not {"name", "metadata"} <= set(reader.fieldnames or ()):
            raise ValueError("no name and metadata columns")
        rows = [(row, json.loads(row["metadata"])) for row in reader]
        if not all(isinstance(meta, dict) for _, meta in rows):
            raise TypeError("metadata is not an object")
    except (csv.Error, ValueError, TypeError) as error:
        return unreadable(app, side, f"advisors: output not readable ({error.__class__.__name__}: {error})")
    mapped = Mapped("advisors")
    for row, meta in rows:
        items = _items(row["name"], meta)
        for flaw, target in items:
            mapped.add(row["name"], flaw, _line(row), **target)
        if not items:
            mapped.skip()
    return mapped.run(app, side)
