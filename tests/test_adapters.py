"""Tests for the baseline adapters and the baseline runner. Saved and hand-written samples only. No Docker."""
import csv
import importlib.util
import io
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from access_review.adapters import ADAPTERS
from access_review.scoring import score

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "baselines"
SCHEMA = Draft202012Validator(json.loads((ROOT / "schemas" / "finding.schema.json").read_text(encoding="utf-8")))
spec = importlib.util.spec_from_file_location("run_baselines", ROOT / "scripts" / "run_baselines.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

TOOLS = sorted(ADAPTERS)
EXT = runner.EXT
KEY = {"app-x": {"flaws_vulnerable": [{"flaw_id": "R1", "table": "profiles"}], "flaws_fixed": []}}


def sample(tool, app, side):
    return (FIXTURES / tool / f"{app}__{side}.{EXT[tool]}").read_text(encoding="utf-8", newline="")


def adapt(tool, text, app="app-x", side="vulnerable"):
    result = ADAPTERS[tool](text, app, side)
    for finding in result["findings"]:
        assert not list(SCHEMA.iter_errors(finding))
        assert finding["status"] == "proved"
    return result


def pairs(result):
    return sorted((f["flaw_id"], f.get("table"), f.get("column"), f.get("function")) for f in result["findings"])


def advisor_csv(*rows):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["name", "title", "level", "metadata"])
    for name, meta in rows:
        writer.writerow([name, name, "WARN", json.dumps(meta)])
    return out.getvalue()


def policy(command, roles, using=False, check=False, name="notes"):
    return ("rls_policy_always_true", {"name": name, "command": command, "roles": roles,
                                       "permissive_using": using, "permissive_with_check": check})


def violation(rule, location, message=""):
    return {"rule_id": rule, "message": message, "location": location}


def pgrls_json(*violations):
    return json.dumps({"violations": list(violations), "skipped_rules": ["PERF003"]})


# --- the vulnerable sample gives exactly the hand-written findings, the fixed side none ---

SAMPLES = {  # tool: (app, hand-written expected findings on the vulnerable side)
    "advisors": ("views-01-bypass", [("V1", "all_notes", None, None)]),
    "rlsautotest": ("rows-01-profiles", [("R1", "profiles", None, None)]),
    "pgrls": ("rows-01-profiles", [("R1", "profiles", None, None)]),
    "semgrep": ("rows-01-profiles", []),
}


@pytest.mark.parametrize("tool", ["advisors", "rlsautotest", "pgrls"])
def test_vulnerable_sample_gives_expected_findings(tool):
    app, expected = SAMPLES[tool]
    result = adapt(tool, sample(tool, app, "vulnerable"), app)
    assert not result["not_checkable"]
    assert pairs(result) == expected
    assert result["findings"][0]["proof"][0]["statement"]  # the raw output line is kept


@pytest.mark.parametrize("tool", ["advisors", "rlsautotest", "pgrls"])
def test_negative_control_and_recall(tool):
    app, expected = SAMPLES[tool]
    key = {"app-x": {"flaws_vulnerable": [{"flaw_id": f, "table": t} for f, t, _, _ in expected],
                     "flaws_fixed": []}}
    vulnerable = adapt(tool, sample(tool, app, "vulnerable"), "app-x")
    fixed = adapt(tool, sample(tool, app, "fixed"), "app-x", "fixed")
    assert fixed["findings"] == []
    full = score([vulnerable, fixed], key)
    assert (full["found"], full["planted"]) == (1, 1)
    dropped = score([{**vulnerable, "findings": []}, fixed], key)
    assert (dropped["found"], dropped["planted"]) == (0, 1)


def test_semgrep_maps_nothing_and_counts_its_items():
    app, _ = SAMPLES["semgrep"]
    text = json.loads(sample("semgrep", app, "vulnerable"))
    assert text["results"] == []
    assert adapt("semgrep", json.dumps(text))["findings"] == []
    text["results"] = [{"check_id": "some.rule", "path": "a.sql"}]
    result = adapt("semgrep", json.dumps(text))
    assert result["findings"] == [] and not result["not_checkable"]
    assert "1 unmapped" in result["notes"][0]
    assert score([result], KEY)["found"] == 0


# --- the mapping tables of docs/baselines.md section 3, row by row ---

def test_advisors_rows():
    text = advisor_csv(
        ("rls_disabled_in_public", {"name": "t1"}), ("policy_exists_rls_disabled", {"name": "t2"}),
        policy("INSERT", ["anon"], name="t3"), policy("INSERT", ["public"], name="t4"),
        policy("INSERT", ["authenticated"], name="t5"),
        policy("UPDATE", ["authenticated"], using=True, check=False, name="t6"),
        policy("UPDATE", ["authenticated"], using=False, check=True, name="t7"),
        policy("DELETE", ["authenticated"], using=True, name="t8"),
        ("security_definer_view", {"name": "v1"}), ("materialized_view_in_api", {"name": "v2"}),
        ("anon_security_definer_function_executable", {"name": "f1"}),
        ("authenticated_security_definer_function_executable", {"name": "f2"}),
        ("sensitive_columns_exposed", {"name": "t9", "sensitive_columns": ["email", "phone"]}),
        # unmapped
        policy("ALL", ["anon"], using=True, name="u1"), policy("SELECT", ["anon"], using=True, name="u2"),
        policy("DELETE", ["authenticated"], using=False, name="u3"),
        ("auth_rls_initplan", {"name": "u4"}), ("rls_enabled_no_policy", {"name": "u5"}),
        ("security_definer_view", {}),
    )
    result = adapt("advisors", text)
    assert pairs(result) == sorted([
        ("R1", "t1", None, None), ("R1", "t2", None, None), ("R3", "t3", None, None), ("R3", "t4", None, None),
        ("R4", "t5", None, None), ("R5", "t6", None, None), ("R7", "t7", None, None), ("R6", "t8", None, None),
        ("V1", "v1", None, None), ("V1", "v2", None, None), ("U3", None, None, "f1"), ("U1", None, None, "f2"),
        ("C2", "t9", "email", None), ("C2", "t9", "phone", None)])
    assert "6 unmapped" in result["notes"][0]


def test_rlsautotest_rows():
    def foot(kind, roles):
        return (f"policy p: SELECT USING (true) -> every {roles} sees ALL rows" if kind == "read"
                else f"policy p: INSERT WITH CHECK (true) -> any {roles} may write any row")
    tables = [
        {"table": "exposed_t", "exposed": True, "footguns": []},
        {"table": "read_anon", "footguns": [foot("read", "['anon', 'authenticated']")]},
        {"table": "read_user", "footguns": [foot("read", "['authenticated']")]},
        {"table": "write_anon", "footguns": [foot("write", "['anon']")]},
        {"table": "write_user", "footguns": [foot("write", "['authenticated']")]},
        {"table": "unmapped_t", "exposed": False, "footguns": ["NOT TESTABLE cells", "UPDATE not fully tested"],
         "idgrid": {"SELECT": {"anon": {"exp": False, "pass": False}, "other": {"exp": False, "pass": True}}}},
    ]
    surfaces = [
        {"object": "v", "type": "view", "why": "view runs with owner's rights and is readable by anon"},
        {"object": "mv", "type": "materialized view", "why": "readable by authenticated"},
        {"object": "f()", "type": "function", "why": "SECURITY DEFINER function is EXECUTE-able by anon"},
        {"object": "g(a uuid)", "type": "function", "why": "is EXECUTE-able by authenticated"},
        {"object": "r", "type": "role", "why": "role is BYPASSRLS"},
        {"object": "t", "type": "table", "why": "RLS is enabled but not FORCED"},
    ]
    result = adapt("rlsautotest", json.dumps({"tables": tables, "bypass_surfaces": surfaces}))
    assert pairs(result) == sorted([
        ("R1", "exposed_t", None, None), ("R1", "read_anon", None, None), ("R2", "read_user", None, None),
        ("R3", "write_anon", None, None), ("R4", "write_user", None, None), ("V1", "v", None, None),
        ("V1", "mv", None, None), ("U3", None, None, "f"), ("U1", None, None, "g")])
    assert "5 unmapped" in result["notes"][0]  # 2 footguns, 1 failed grid cell, 2 bypass surfaces


def test_pgrls_rows():
    text = pgrls_json(
        violation("SEC001", "public.a"), violation("SEC038", "public.b.some policy"),
        violation("SEC049", "public.c", "grants SELECT to anon, authenticated"),
        violation("SEC039", "public.d.p"), violation("SEC028", "public.e.p"),
        violation("SEC006", "public.f.p", "covers UPDATE but has no WITH CHECK"),
        violation("SEC020", "public.g.p"),
        # unmapped
        violation("SEC049", "public.h", "grants SELECT to authenticated"),
        violation("SEC006", "public.i.p", "covers INSERT"), violation("SEC008", "public.j.p"),
        violation("SEC002", "public.k"), violation("SEC001", "nolocation"))
    result = adapt("pgrls", text)
    assert pairs(result) == [(flaw, table, None, None) for flaw, table in
                             [("R1", "a"), ("R1", "b"), ("R1", "c"), ("R3", "d"), ("R4", "e"), ("R7", "f"),
                              ("R7", "g")]]
    assert "5 unmapped" in result["notes"][0]
    assert "1 rule(s) skipped" in result["notes"][1]


def test_same_flaw_and_target_is_one_finding_with_both_proofs():
    result = adapt("pgrls", pgrls_json(violation("SEC001", "public.a"), violation("SEC038", "public.a.p")))
    assert pairs(result) == [("R1", "a", None, None)]
    assert len(result["findings"][0]["proof"]) == 2


def test_names_drop_schema_and_quotes():
    text = advisor_csv(("security_definer_view", {"name": '"public"."all_notes"'}),
                       ("anon_security_definer_function_executable", {"name": "public.fn(a uuid)"}))
    assert pairs(adapt("advisors", text)) == [("U3", None, None, "fn"), ("V1", "all_notes", None, None)]


# --- unreadable output is never a clean empty result ---

GARBAGE = ["", "not json at all", "{", "[]", '{"unexpected": 1}', "\x00\x01\x02", "<html>502</html>"]


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("text", GARBAGE)
def test_garbage_is_not_checkable(tool, text):
    result = adapt(tool, text)
    assert result["not_checkable"] is True
    assert result["findings"] == [] and result["notes"]
    assert score([result], KEY)["not_checkable"] == 1


def test_not_checkable_specifics():
    assert adapt("advisors", "name,metadata\nrls_disabled_in_public,{not json}\n")["not_checkable"]
    scanned = {"results": [], "errors": [], "paths": {"scanned": []}}
    assert adapt("semgrep", json.dumps(scanned))["not_checkable"]  # nothing scanned is not a clean scan
    failed = {**scanned, "errors": [{"message": "x"}], "paths": {"scanned": ["a"]}}
    assert adapt("semgrep", json.dumps(failed))["not_checkable"]
    assert adapt("pgrls", json.dumps({"violations": [{"rule_id": "SEC001"}]}))["not_checkable"]
    assert adapt("rlsautotest", json.dumps({"tables": [{"exposed": True}], "bypass_surfaces": []}))["not_checkable"]


# --- the saved fixtures: all 36 parse, and the false alarms are the documented ones ---

def fixture_names(tool):
    return sorted(p.stem for p in (FIXTURES / tool).glob(f"*.{EXT[tool]}"))


@pytest.mark.parametrize("tool", TOOLS)
def test_all_saved_fixtures_parse(tool):
    names = fixture_names(tool)
    assert len(names) == 36
    for name in names:
        app, side = name.split("__")
        result = adapt(tool, sample(tool, app, side), app, side)
        assert not result["not_checkable"], (name, result["notes"])


# Docs section 2.7: mapped items on fixed or clean runs, over all 36 runs per tool.
FALSE_ALARMS = {
    "semgrep": [],
    "advisors": [("functions-02-security-definer-no-check", "fixed", "U1", "set_note_body")],
    "rlsautotest": [("columns-03-phone-exposed", "fixed", "R1", "directory"),
                    ("decoy-01-public-posts", "migrations", "R1", "posts"),
                    ("decoy-02-public-profile-read", "migrations", "R1", "profiles_public"),
                    ("functions-02-security-definer-no-check", "fixed", "U1", "set_note_body")],
    "pgrls": [("columns-03-phone-exposed", "fixed", "R1", "directory"),
              ("decoy-01-public-posts", "migrations", "R1", "posts"),
              ("decoy-02-public-profile-read", "migrations", "R1", "profiles_public")],
}


@pytest.mark.parametrize("tool", TOOLS)
def test_mapped_false_alarms_are_the_documented_ones(tool):
    found = []
    for name in fixture_names(tool):
        app, side = name.split("__")
        if side == "vulnerable":
            continue
        for finding in adapt(tool, sample(tool, app, side), app, side)["findings"]:
            found.append((app, side, finding["flaw_id"], finding.get("table") or finding.get("function")))
    assert sorted(found) == sorted(FALSE_ALARMS[tool])


# --- the runner, with the command layer faked ---

def make_folder(tmp_path, sides=("vulnerable", "fixed")):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "answer_key.json").write_text(json.dumps(KEY), encoding="utf-8")
    for side in sides:
        migrations = tmp_path / "app-x" / side / "migrations"
        migrations.mkdir(parents=True)
        (migrations / "001_init.sql").write_text("-- sql", encoding="utf-8")
    return tmp_path


def test_runner_saves_raw_output_and_run_objects(tmp_path):
    folder, out = make_folder(tmp_path / "apps"), tmp_path / "out"
    texts = {side: sample("pgrls", "rows-01-profiles", side) for side in ("vulnerable", "fixed")}
    calls = []

    def fake(argv):
        calls.append(argv)
        side = "fixed" if "fixed" in " ".join(argv) else "vulnerable"
        return 1, texts[side], ""  # pgrls exits 1 when it reports violations

    assert runner.main([str(folder), "--tool", "pgrls", "--out", str(out)], fake) == 0
    assert len(calls) == 2 and all("--network" in c and "none" in c for c in calls)
    assert (out / "raw" / "app-x__vulnerable.json").read_text(encoding="utf-8") == texts["vulnerable"]
    runs = [json.loads((out / f"app-x__{side}.json").read_text(encoding="utf-8")) for side in ("vulnerable", "fixed")]
    assert [(r["app"], r["side"], r["not_checkable"]) for r in runs] == [
        ("app-x", "vulnerable", False), ("app-x", "fixed", False)]
    assert pairs(runs[0]) == [("R1", "profiles", None, None)] and runs[1]["findings"] == []
    assert score(runs, KEY)["found"] == 1


def test_runner_failed_command_is_not_checkable(tmp_path):
    folder = make_folder(tmp_path / "apps", sides=("vulnerable",))
    for fake in (lambda argv: (2, "", "boom"), lambda argv: (0, "garbage", ""), _missing):
        out = tmp_path / f"out{id(fake)}"
        assert runner.main([str(folder), "--tool", "pgrls", "--out", str(out)], fake) == 0
        run = json.loads((out / "app-x__vulnerable.json").read_text(encoding="utf-8"))
        assert run["not_checkable"] is True and run["findings"] == [] and run["notes"]


def _missing(argv):
    raise FileNotFoundError("docker")


def test_runner_commands(tmp_path):
    folder = make_folder(tmp_path / "apps")
    migrations = folder / "app-x" / "vulnerable" / "migrations"
    assert runner.command("semgrep", folder, migrations) == "semgrep needs --rules"
    semgrep = runner.command("semgrep", folder, migrations, tmp_path / "rules")
    assert semgrep[-1] == "planted/app-x/vulnerable/migrations" and "--metrics" in semgrep and "--json" in semgrep
    assert "planted/app-x/vulnerable/migrations/001_init.sql" in runner.command("pgrls", folder, migrations)
    (migrations / "002.sql").write_text("-- more", encoding="utf-8")
    assert isinstance(runner.command("pgrls", folder, migrations), str)
    assert runner.command("advisors", folder, migrations)[-1] == str(migrations)


# --- pgrls on an app with several migration files (docs/baselines.md 2.5) ---

def two_file_folder(tmp_path, names=("001_a.sql", "002_b.sql")):
    folder = make_folder(tmp_path / "apps", sides=("vulnerable",))
    migrations = folder / "app-x" / "vulnerable" / "migrations"
    (migrations / "001_init.sql").unlink()
    for name in names:
        (migrations / name).write_text("-- sql", encoding="utf-8")
    return folder


def run_pgrls(folder, tmp_path, outputs):
    """Run the runner with the command layer faked; outputs maps a file name to (exit code, text)."""
    calls = []

    def fake(argv):
        calls.append(argv[-3].rsplit("/", 1)[-1])
        code, text, *err = outputs[calls[-1]]
        return code, text, (err or [""])[0]

    out = tmp_path / "out"
    assert runner.main([str(folder), "--tool", "pgrls", "--out", str(out)], fake) == 0
    return json.loads((out / "app-x__vulnerable.json").read_text(encoding="utf-8")), calls, out


def test_pgrls_two_files_each_finding_once_and_in_order(tmp_path):
    folder = two_file_folder(tmp_path)
    a, b = pgrls_json(violation("SEC001", "public.a")), pgrls_json(violation("SEC039", "public.b.p"),
                                                                   violation("SEC002", "public.z"))
    run, calls, out = run_pgrls(folder, tmp_path, {"001_a.sql": (1, a), "002_b.sql": (1, b)})
    assert calls == ["001_a.sql", "002_b.sql"] and not run["not_checkable"]
    assert pairs(run) == [("R1", "a", None, None), ("R3", "b", None, None)]
    assert "1 unmapped" in run["notes"][0]
    assert [p["statement"][:9] for f in run["findings"] for p in f["proof"]] == ["001_a.sql", "002_b.sql"]
    assert (out / "raw" / "app-x__vulnerable__002_b.sql.json").read_text(encoding="utf-8") == b


def test_pgrls_duplicate_across_files_is_one_finding(tmp_path):
    folder = two_file_folder(tmp_path)
    same = pgrls_json(violation("SEC001", "public.a"))
    run, _, _ = run_pgrls(folder, tmp_path, {"001_a.sql": (1, same), "002_b.sql": (1, same)})
    assert pairs(run) == [("R1", "a", None, None)] and len(run["findings"][0]["proof"]) == 2


def test_pgrls_failing_second_file_is_not_checkable(tmp_path):
    folder = two_file_folder(tmp_path)
    good = pgrls_json(violation("SEC001", "public.a"))
    for bad in ((2, "", "boom"), (0, "garbage", ""), (1, "{}", "")):
        run, _, _ = run_pgrls(folder, tmp_path / str(id(bad)), {"001_a.sql": (1, good), "002_b.sql": bad})
        assert run["not_checkable"] is True and run["findings"] == [] and "002_b.sql" in run["notes"][0]


def test_pgrls_no_sql_file_is_not_checkable(tmp_path):
    folder = two_file_folder(tmp_path, names=())
    run, calls, _ = run_pgrls(folder, tmp_path, {})
    assert run["not_checkable"] is True and run["findings"] == [] and calls == []


def test_pgrls_one_file_equals_the_single_file_result(tmp_path):
    text = sample("pgrls", "rows-01-profiles", "vulnerable")
    folder = two_file_folder(tmp_path, names=("001_init.sql",))
    run, _, out = run_pgrls(folder, tmp_path, {"001_init.sql": (1, text)})
    assert run == adapt("pgrls", text)
    assert (out / "raw" / "app-x__vulnerable.json").read_text(encoding="utf-8") == text


def test_pgrls_negative_control_second_files_finding_counts(tmp_path):
    a, b = pgrls_json(violation("SEC001", "public.a")), pgrls_json(violation("SEC039", "public.b.p"))
    both = run_pgrls(two_file_folder(tmp_path / "x"), tmp_path / "x", {"001_a.sql": (1, a), "002_b.sql": (1, b)})[0]
    without = run_pgrls(two_file_folder(tmp_path / "y"), tmp_path / "y",
                        {"001_a.sql": (1, a), "002_b.sql": (0, pgrls_json())})[0]
    assert len(both["findings"]) == len(without["findings"]) + 1
