"""Run every reference fix through recheck and save one run object per attempt.

python -m fix_check run reference --out DIR [--fixes fixes/reference] [--planted planted]
One attempt is one app and its fix file. The attempts run one at a time, because each uses Docker.
"""
import json
from pathlib import Path

from access_review.scoring import load_key
from fix_check.recheck import NAMES, NOT_RUN, CannotRun, recheck

REFUSED = "the fix was refused"


def apps_in_plan(planted):
    """The plan's rule (docs/fixcheck-plan.md section 2): a planted flaw on the vulnerable side and both folders."""
    planted = Path(planted)
    key = load_key(planted / "answer_key.json")
    return [n for n, v in key.items()
            if v["flaws_vulnerable"] and (planted / n / "vulnerable").is_dir() and (planted / n / "fixed").is_dir()]


def _fails_condition_1(app, reason):
    conditions = {str(n): {"result": NOT_RUN, "detail": ""} for n in NAMES}
    conditions["1"] = {"result": "fail", "detail": reason}
    return {"app": app, "conditions": conditions, "broken": [1], "notes": [], "works": False}


def attempt(app_dir, fix, key):
    """One attempt. A missing, empty or refused fix fails condition 1 and still counts."""
    fix = Path(fix)
    if not fix.is_file():
        return _fails_condition_1(app_dir.name, f"there is no fix file {fix.name}")
    try:
        return recheck(app_dir, fix, key)
    except CannotRun as error:
        if str(error).startswith(REFUSED):
            return _fails_condition_1(app_dir.name, str(error))
        return {"app": app_dir.name, "cannot_run": str(error), "broken": [], "works": False}


def run_reference(out, fixes="fixes/reference", planted="planted", apps=None):
    """Run the attempts one at a time, save DIR/<app>__1.json for each, print one line each, return the runs."""
    planted, fixes, out = Path(planted), Path(fixes), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    key = load_key(planted / "answer_key.json")
    runs = []
    for name in apps or apps_in_plan(planted):
        fix = fixes / f"{name}.sql"
        run = attempt(planted / name, fix, key)
        run.update({"attempt": 1, "fix_file": str(fix)})
        (out / f"{name}__1.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        runs.append(run)
        print(line(run), flush=True)
    return runs


def line(run):
    if "cannot_run" in run:
        return f'{run["app"]}__1: cannot run - {run["cannot_run"]}'
    return f'{run["app"]}__1: ' + ("ok" if run["works"] else "fails " + "+".join(map(str, run["broken"])))


def totals(runs):
    n = len(runs)
    broke = {c: sum(c in r["broken"] for r in runs) for c in NAMES}
    cannot = sum("cannot_run" in r for r in runs)
    ok = sum(r["works"] for r in runs)
    return (f"Reference: {n} attempts, {ok} of {n} succeeded, broke 1: {broke[1]}, broke 2: {broke[2]}, "
            f"broke 3: {broke[3]}, broke 4: {broke[4]}, could not run: {cannot}")
