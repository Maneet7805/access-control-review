"""Pytest plugin for test_teeth.py. Replaces one probe with a broken copy when TEETH="probe:mode" is set.

mode "clean": the probe always reports a refusal and no rows. mode "leak": it always reports a row that breaks
the rule. The real probe still runs first, so the sandbox, the actor and the statement stay real.
"""
import json
import os
from dataclasses import replace

from access_review import probes

PAIRS = {"user_writes_protected_columns", "visitor_reads_private_columns", "user_reads_private_columns"}
NAMES = ("SELECT coalesce(json_agg(column_name), '[]') FROM information_schema.columns "
         "WHERE table_schema = 'public' AND table_name = '{}'")


def _break(evidence, mode, row):
    if mode == "clean":
        return replace(evidence, result="permission_denied", rows_seen=[], error="teeth: broken probe")
    return replace(evidence, result="ok", rows_seen=[row], error=None)


def _row(box, args, evidence):
    """One row with a value in every column; the owner column is the actor's own id only for the C1 probe."""
    thing = args[0]
    if isinstance(thing, dict):  # a function call returns a value, not table columns
        return {"result": "leak"}
    row = dict.fromkeys(json.loads(box.run(NAMES.format(thing))), "leak")
    if evidence.probe == "user_writes_protected_column":
        row[args[1]] = evidence.actor.removeprefix("user:")
    return row


def _wrap(name, mode):
    real = getattr(probes, name)

    def broken(box, *args):
        out = real(box, *args)
        if name in PAIRS:
            return [(column, _break(item, mode, _row(box, args, item))) for column, item in out]
        return _break(out, mode, _row(box, args, out))

    return broken


_probe, _, _mode = os.environ.get("TEETH", "").partition(":")
if _probe:
    setattr(probes, _probe, _wrap(_probe, _mode))
