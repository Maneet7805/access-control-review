"""The AI fix source: give an AI only the report's fix text, save everything it said, turn its answer into one fix file.

python -m fix_check run ai --out DIR --ask-cmd "<command>"
The AI answer is untrusted text. It is never run on the host: it only becomes a fix file that recheck applies inside
the sandbox. The AI gets the prompt and nothing else (no tools, no files). No retry.
"""
import json
import re
import shlex
import subprocess
from pathlib import Path

from access_review.cli import review
from access_review.report import _plain
from access_review.sandbox import NotCheckable, sandbox
from access_review.scoring import load_key
from fix_check.run import apps_in_plan, attempt, line

PLAN = Path(__file__).resolve().parents[2] / "docs" / "fixcheck-plan.md"
ATTEMPTS = 3  # per app, from docs/fixcheck-plan.md section 3
BLOCK = re.compile(r"```[ \t]*(?:sql)?[ \t]*\r?\n(.*?)```", re.DOTALL | re.IGNORECASE)


def saved_prompt(plan=PLAN):
    """The one saved prompt: the fenced block of the plan that holds {FIX_TEXT}."""
    text = Path(plan).read_text(encoding="utf-8").replace("\r\n", "\n")
    blocks = [b for b in re.findall(r"```\n(.*?)\n```", text, re.DOTALL) if "{FIX_TEXT}" in b]
    if len(blocks) != 1:
        raise ValueError("the plan must hold exactly one prompt with {FIX_TEXT}")
    return blocks[0]


def fix_text(findings):
    """Only the 'Suggested fix' sentence of every proved finding, in report order, one paragraph each."""
    ordered = sorted(findings, key=lambda f: f.status != "proved")
    return "\n\n".join(_plain(f.fix) for f in ordered if f.status == "proved")


def sql_from(answer):
    """The text inside the answer's sql or untagged code blocks, joined with a blank line. No block: empty."""
    blocks = [b.strip() for b in BLOCK.findall(answer)]
    return "\n\n".join(b for b in blocks if b)


def ask_ai(text, ask):
    """Build the prompt from the fix text, call `ask(prompt)` once, return (prompt, raw answer, sql)."""
    prompt = saved_prompt().replace("{FIX_TEXT}", text)
    answer = ask(prompt)
    answer = answer if isinstance(answer, str) else ""
    return prompt, answer, sql_from(answer)


def command_ask(command, timeout=600):
    """The real `ask`: run the user's AI command with the prompt on stdin and read stdout. No shell, no files."""
    argv = shlex.split(command)

    def ask(prompt):
        done = subprocess.run(argv, input=prompt, capture_output=True, text=True, timeout=timeout, check=True)  # nosec B603
        return done.stdout

    return ask


def vulnerable_findings(app_dir):
    """Review the vulnerable app (Docker). Returns the findings, or raises NotCheckable."""
    with sandbox(Path(app_dir) / "vulnerable" / "migrations", baseline=True) as box:
        return review(box)[0]


def _write(path, text):
    path.write_text(text, encoding="utf-8", newline="")


def run_ai(out, ask, fixes="fixes/ai", planted="planted", apps=None, attempts=ATTEMPTS,
           findings_of=vulnerable_findings, judge=attempt):
    """Per app and attempt: save prompt, answer, fix under fixes/<app>/<n>/, run recheck, save a run object."""
    planted, fixes, out = Path(planted), Path(fixes), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    key = load_key(planted / "answer_key.json")
    runs, errors = [], []

    def safe_ask(prompt):  # an AI that fails is an attempt that fails: recorded, never retried
        try:
            return ask(prompt)
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}")
            return ""

    for name in apps or apps_in_plan(planted):
        try:
            text, failure = fix_text(findings_of(planted / name)), None
        except NotCheckable as error:
            text, failure = "", f"the vulnerable app cannot be reviewed: {error}"
        for n in range(1, attempts + 1):
            folder = fixes / name / str(n)
            if (folder / "answer.txt").exists():
                raise ValueError(f"{folder} already holds a recorded attempt; none is replaced or repeated")
            folder.mkdir(parents=True, exist_ok=True)
            if failure:
                run = {"app": name, "cannot_run": failure, "broken": [], "works": False}
            else:
                errors.clear()
                prompt, answer, sql = ask_ai(text, safe_ask)
                _write(folder / "prompt.txt", prompt)
                _write(folder / "answer.txt", answer)
                _write(folder / "fix.sql", sql)
                run = judge(planted / name, folder / "fix.sql", key)
                if errors:
                    run.setdefault("notes", []).append(f"The AI could not be asked: {errors[0]}")
            run.update({"attempt": n, "fix_file": str(folder / "fix.sql"), "prompt_file": str(folder / "prompt.txt"),
                        "answer_file": str(folder / "answer.txt")})
            _write(out / f"{name}__{n}.json", json.dumps(run, indent=2, sort_keys=True) + "\n")
            runs.append(run)
            print(line(run), flush=True)
    return runs
