# Roadmap: access-control-review

Put this file at `docs/ROADMAP.md`. Claude Code reads it, picks the next eligible task, builds it, proves it works, ticks the box and reports. Maneet supervises and merges.

How much detail each part has:
- M0 to M4 are written in full. They are the current work and the next work.
- M5 and M6 are written in full. M7 is medium detail. It is rewritten in full when its turn comes.
- M8 to M10 are goals and decision points only. Details written months early go stale, and they depend on what M1 and M2 teach us.

## 1. Where we are (the agent updates this after every PR)

| Milestone | Plain-English purpose | Progress |
| --- | --- | --- |
| M0 Harness | Repo, CI, rules, roadmap | 7/7 |
| M1 Honest foundations | A sandbox that behaves like real Supabase, is safe, and checks allowed access too | 8/9 |
| M2 Thin slice | One app, one attack, one plain-language report, end to end | 6/6 |
| M3 More attacks | Write rows, protected columns, views, functions, plus decoy apps | 9/9 |
| M4 Evaluation frozen | Scoring rules, held-out test apps and a freeze tag, before any scoring | 5/5 |
| M5 Compare | Run other tools on the same apps and score everyone | 6/6 |
| M6 Fix check | Does the suggested fix remove the flaw without breaking the app | 1/9 |
| M7 Real apps | Unscored case studies on public apps | 0/4 |
| M8 Questions | Ask the developer when the code cannot decide | later |
| M9 Delivery | GitHub Action, then a local web page | later |
| M10 Handover | Docs, install experience, evidence pack for the report | later |

- Current milestone: M6
- Last merged PR: #77
- Next eligible task: M6.2
- Open decisions waiting for Maneet: see section 6

## 2. The flow, and what each stage hands to the next

1. **Sandbox** builds a throwaway database from the app's migration files, behaving like Supabase. Hands over: a connection that can act as a visitor or as a signed-in user.
2. **Probes** try to read and change data as each actor. Hands over: evidence (what was run, what came back).
3. **Findings** turn evidence into a proven problem with an explanation and a fix. Hands over: findings in JSON.
4. **Report** shows findings in plain language. Hands over: `report.md`.
5. **Scoring** compares findings with the answer key. Hands over: recall, precision, false alarms.
6. **Comparison** runs other tools on the same apps and scores them the same way.
7. **Fix check** applies a fix and attacks again.
8. **Questions, Action, web page** wrap the engine so developers can use it.

The build order differs from the flow order. We build the middle first (1 to 4) as one thin slice, then widen it.

## 3. Rules for the agent (strict)

1. One task per pull request. Branch name `task/M1.2-short-name`. Never expand scope.
2. Take only the first unchecked task whose `Depends on` are all checked, and which is not a DECISION or an owner gate. If none is eligible, stop and say why.
3. Never tick an owner gate (G0 to G6). You may tick a decision after you have recorded it in ASSUMPTIONS.md.
4. Never edit the checkbox of another task. In your own PR, tick your task and update section 1.
5. Every task needs a test that can fail. For every probe and every score, show a negative control: it fires on the flawed app and stays silent on the fixed twin.
6. Never weaken, skip or delete a test to make it pass. If a test seems wrong, stop and ask.
7. Never change `planted/answer_key.json` while writing probes to match your code. The key is written from the flaw catalogue (Appendix A), not from what the probe finds. Key changes go in their own PR and need Maneet's approval.
8. The language model never decides a finding. Execution decides.
9. Never write "secure" about an app. Only "No violation found under this test."
10. Real public repos are private material. Never commit owner names, repo URLs or scan output. Use cover names. `private/`, `cases/`, `scans/` stay ignored.
11. Read any web page you rely on in full before using it. Quote at most one line of it.
12. You decide engineering and method choices yourself (libraries, file layout, names, how to test, which option fits best, which baselines, which case-study apps). When you decide, do not wait: pick the simplest option that is easy to change later, add an entry to ASSUMPTIONS.md (date, the options you saw, what you picked, why), mention it in the pull request, and carry on. I can reverse it in review. Stop and ask me only when the choice:
    1. costs money, or needs a paid service or a new account,
    2. would put a real app's name, URL, code or scan output into a committed file,
    3. changes the answer key, the scoring rules or docs/EVALUATION.md (put those in their own pull request for my review),
    4. would force you to weaken or delete a test.

    Put questions in the pull request description under 'Confirm next', not in chat.
13. Report in the format in CLAUDE.md. Paste the validation commands you ran and one line of their output.
14. No time estimates anywhere. Plain English. No emojis.

## 4. Task format

Each task has: ID, depends on, goal, files (touch and do not touch), steps, validation (exact commands plus the assertion that proves the goal), done when, stop and ask if.

Definition of done for every task, in addition to its own:
- `ruff check .`, `pytest -v`, `bandit -r src -ll`, `pip-audit --skip-editable` pass locally and CI is green.
- The task's checkbox is ticked and section 1 is updated, in the same PR.
- The PR description lists what was run and the real output (one line each).

## 5. How Maneet reviews a pull request (3 minutes)

1. CI is green.
2. The PR touches only the files the task lists.
3. The task's checkbox is ticked and section 1 matches.
4. The validation output is pasted and says what the task asked for.
5. Run the demo command if the task has one. You see what the task says you should see.
6. Tests were not weakened (the diff does not delete assertions).
7. Merge. If anything fails, comment on the PR. Do not merge.

## 6. Decisions (the agent decides these; see rule 12)

| ID | Question | Options | Who decides, and notes |
| --- | --- | --- | --- |
| D1 | Sandbox base image | A: `postgres:16` plus our own Supabase stubs. B: Supabase's database image | AGENT-decides. Decided, option B (already recorded). |
| D2 | How probes reach a database that has no network | A: run statements through `docker exec`. B: unix socket. C: internal network plus a probe container | AGENT-decides. Option A, decided 13 Nov: no network, no extra containers. |
| D3 | Who writes the held-out apps | A: a fresh Claude session given only the flaw catalogue. B: you. C: a classmate | AGENT-decides. A separate helper session sees only Appendix A, never the code, and writes the held-out apps. Maneet reviews the key at G4. |
| D4 | Which existing tools are the baselines | Semgrep, Supabase advisors, rlsautotest, pgrls, rlsgrid, SupaShield | AGENT-decides. Baselines must be free, run locally with no network, and cover rows, columns or functions. The set includes Semgrep, the Supabase advisors, and at least one execution-based database tool from Chapter 2 Table 2. Write the choice and the reason for each in docs/baselines.md and commit it BEFORE the held-out run. After that run it cannot change. |
| D5 | Which AI applies the fixes in M6, and how many runs | Claude Code, others | AGENT-decides. The agent chooses which AI applies the fixes in M6 and how many runs. Record the choice. |
| D6 | Which public apps become case studies | Needs licence check | AGENT-decides. Case-study apps must be public, have a licence that permits use, show evidence of being AI-built, have real migrations, and rebuild cleanly in the sandbox. The numbers mentioned earlier (for example 80 percent AI commits) are soft starting figures: the agent may adjust them, but records why. Keep the candidate list with names and URLs only in the git-ignored private/ folder. Commit cover names only. |

## 7. Milestones

### M0 Harness

- [x] M0.1 Repo with CI (tests, ruff, bandit, pip-audit, CodeQL, secret scan) and Dependabot. PR #17.
- [x] M0.2 CLAUDE.md, CODING.md, README, SECURITY.md. PRs #16, #18.
- [x] M0.3 Sandbox plus visitor read probe plus planted `rows-01-profiles`. PR #14.
- [x] M0.4 Signed-in user read probe plus planted `rows-02-profiles-all-authenticated`. PR #15.
- [x] **M0.5 Add the project context to the repo.**
  - Depends on: none.
  - Goal: Claude Code has the project rules and the big picture without asking.
  - Files: create `docs/ROADMAP.md` (this file), `docs/HANDOVER.md`, `ASSUMPTIONS.md`, `.github/pull_request_template.md` (the section 5 checklist).
  - Validation: `ruff check .` and `pytest -v` still pass. Open the PR and check the template appears.
  - Done when: the three docs and the template are merged.
- [x] **M0.6 Point CLAUDE.md at the roadmap.**
  - Depends on: M0.5.
  - Goal: every session starts by reading `docs/ROADMAP.md` and `docs/HANDOVER.md`.
  - Files: `CLAUDE.md` (add a short section only, remove nothing).
  - Validation: a fresh session reads the roadmap and names the next eligible task correctly.
  - Stop and ask if: you think any existing rule should change.
- [x] **M0.7 One command that runs every check.**
  - Depends on: M0.5.
  - Goal: one command prints PASS or FAIL for all four checks, on Windows and Linux.
  - Files: `scripts/check.py`. Do not touch: CI files.
  - Validation: `python scripts/check.py` passes on a clean tree. Break one test on purpose and the script must report FAIL (negative control).
  - Done when: README and CODING.md mention the command.
- [x] **G0 (owner).** Maneet runs `python scripts/check.py`, sees PASS, and reads `docs/ROADMAP.md` once.

### M1 Honest foundations

Why first: right now the test apps create their own roles and read identity from a made-up setting. A real Supabase app will not rebuild. If the foundation is fake, everything after it is evaluated on a fake.

- [x] **M1.1 DECISION D1 spike: what does each base image provide?**
  - Depends on: M0.7.
  - Goal: a written answer, with evidence, to "what does Supabase's database image give us that `postgres:16` does not".
  - Files: create `docs/decisions/sandbox-image.md`, `scripts/probe_images.py`. Do not touch `src/`.
  - Steps: start each image. Query `pg_roles` (anon, authenticated, service_role, their attributes), `pg_namespace` (auth, storage), `pg_proc` (auth.uid, auth.role, auth.jwt), `pg_extension`, and the default privileges on schema `public`. Read the Supabase pages on row level security and on the local development setup in full before writing.
  - Validation: `python scripts/probe_images.py` prints one table per image. The document has the table, the memory used by each image at idle, and a recommendation.
  - Done when: Maneet picks A or B (D1) in the PR.
- [x] **M1.2 Supabase baseline in the sandbox.**
  - Depends on: M1.1 and D1 decided.
  - Goal: after the baseline loads, a typical AI-built Supabase migration applies without errors.
  - Files: `src/access_review/baseline.sql` (only what the image lacks), `src/access_review/sandbox.py`, `tests/test_baseline.py`. Do not touch: `planted/`.
  - What the baseline must provide: roles `anon`, `authenticated`, `service_role` with their real attributes (service_role bypasses row security); schema `auth` with `auth.users`; `auth.uid()`, `auth.role()`, `auth.jwt()` reading `request.jwt.claims`; the default privileges Supabase sets on `public`, so that a table with row security off is fully open to `anon` and `authenticated`, as in real life. Confirm each item against the Supabase docs and cite the page.
  - Validation: `pytest tests/test_baseline.py` applies four fixture migrations that mimic real ones (a table with `user_id uuid references auth.users`, a policy using `auth.uid()`, a trigger on `auth.users`, a function with `security definer`). All apply. Negative control: the same fixtures against bare `postgres:16` fail.
  - Stop and ask if: the baseline needs a Supabase service we cannot run locally.
- [x] **M1.3 Identity helpers: act as a visitor or a signed-in user.**
  - Depends on: M1.2.
  - Goal: `as_visitor` and `as_user(uuid)` set role and `request.jwt.claims` so `auth.uid()` returns the right value.
  - Files: `src/access_review/identity.py`, `src/access_review/probes.py` (replace `app.user_id`), `tests/test_identity.py`.
  - Validation: under `as_user(A)`, `auth.uid()` equals A. Under `as_visitor`, it is null. Under `as_user(A)` then `as_user(B)` on the same connection, no leftover identity from A.
  - Done when: no occurrence of `app.user_id` remains in `src/`.
- [x] **M1.4 Rewrite the two planted apps in real Supabase style, and extend the answer key.**
  - Depends on: M1.3.
  - Goal: planted apps look like AI-built Supabase apps and the key says exactly what is wrong and what must keep working.
  - Files: `planted/rows-01-profiles/**`, `planted/rows-02-profiles-all-authenticated/**`, `planted/answer_key.json`, `tests/test_planted.py`.
  - Rules: no `CREATE ROLE` in migrations. Owners are `uuid references auth.users`. Seed two users. Key shape is in Appendix B. The flaw ids come from Appendix A.
  - Validation: `pytest tests/test_planted.py` passes. The flaws and fixes are the same as before, only the plumbing changed.
  - Needs Maneet's approval because it changes the key (rule 7).
- [x] **M1.5 "Still works" check.**
  - Depends on: M1.4.
  - Goal: fixed twins prove that allowed access survives, not only that nothing leaks.
  - Files: `planted/answer_key.json` (the `allowed` list), a new app `planted/rows-03-locked-out/`, `tests/test_planted.py`.
  - Validation: for every fixed twin, user A reads their own row (assertion). `rows-03-locked-out` has a policy `USING (false)` and must FAIL the allowed check (negative control). That failure is expected and is recorded in the key as `expected_failure: locks_out_owner`.
- [x] **M1.6 Sandbox hardening.** Needs DECISION D2.
  - Depends on: M1.2, D2 decided.
  - Goal: a stranger's migration cannot reach the network or run with more power than needed.
  - Files: `src/access_review/sandbox.py`, `tests/test_sandbox_hostile.py`, `planted/hostile-01-callout/`.
  - Must do: apply migrations with no network; drop all Linux capabilities and add back only what the image needs to start (find out by test); no new privileges; memory, CPU and process limits; the container is removed afterwards even on crash.
  - Validation: a hostile migration that tries a program call out to the internet (for example `COPY ... TO PROGRAM`) must not reach the network; the test asserts the call fails. Another hostile migration that loops forever must be killed by the limits. Negative control: the same hostile migration against the old sandbox settings reaches the network (record this once, then delete that test).
  - Done when: the TODOs in `sandbox.py` about isolation are removed.
- [x] **M1.7 "Not checkable" reports.**
  - Depends on: M1.2.
  - Goal: when an app cannot be rebuilt, the tool says why, in plain words.
  - Files: `src/access_review/sandbox.py`, `tests/test_not_checkable.py`, fixtures under `tests/fixtures/broken/`.
  - Validation: three broken migration fixtures (missing extension, reference to an unknown schema, syntax error) each give a distinct reason string and the line number. Negative control: a good fixture gives no reason.
- [x] **M1.8 Demo command for G1.**
  - Depends on: M1.2, M1.5.
  - Goal: G1 can be run. `python -m access_review.demo_sandbox <migrations folder>` prints how many rows a visitor, user A and user B can read.
  - Files: `src/access_review/demo_sandbox.py`, `tests/test_demo_sandbox.py`.
  - Validation: vulnerable `rows-01-profiles` gives 2, 2, 2. Negative control: its fixed twin gives 0, 1, 1. A broken app prints the plain reason.
- [x] **G1 (owner).** Maneet runs `python -m access_review.demo_sandbox planted/rows-01-profiles/vulnerable/migrations` and sees a short table of what a visitor, user A and user B can see. Expected: visitor 2 rows, A 2 rows, B 2 rows for the vulnerable app. Maneet signs off or rejects.

### M2 Thin slice (one app, one attack, one plain report)

Why: you get the whole flow working once, early. After this, widening is repeating a known pattern.

- [x] **M2.1 Evidence model.**
  - Depends on: G1.
  - Goal: a probe returns what it ran and what it saw, not raw rows.
  - Files: `src/access_review/evidence.py`, `src/access_review/probes.py`, `tests/test_evidence.py`.
  - Shape: `{probe, actor, statement, result, rows_seen, error}`. Serialises to JSON.
  - Validation: round-trip to JSON and back is equal. The two existing probes return evidence. Existing planted tests still pass.
- [x] **M2.2 Finding model and JSON schema, version 0.1.**
  - Depends on: M2.1.
  - Goal: one fixed shape for a finding that later parts can rely on.
  - Files: `src/access_review/findings.py`, `schemas/finding.schema.json`, `tests/test_findings.py`.
  - Fields: `schema_version`, `id`, `flaw_id` (Appendix A), `owasp`, `table` or `column` or `function`, `actor`, `proof` (evidence), `explanation`, `fix`, `status`. Status is only `proved` or `needs_decision`. Nothing is `proved` without evidence.
  - Validation: sample findings validate against the schema. A finding with no evidence is rejected (negative control).
- [x] **M2.3 First rule: another user's rows are readable.**
  - Depends on: M2.2.
  - Goal: turn evidence from `user_reads_rows` into a finding.
  - Files: `src/access_review/rules.py`, `tests/test_rules.py`.
  - Logic: if the table has an owner column that references `auth.users` and the actor sees rows owned by someone else, the finding is `proved`. If the table has no owner column and a visitor can read it, the status is `needs_decision` (it may be public on purpose). Never guess intent.
  - Validation: `rows-01` and `rows-02` vulnerable give one proved finding each. Both fixed twins give none. A new decoy `decoy-01-public-posts` (a table meant to be public, no owner column) gives `needs_decision` and not `proved`. Update the key for it (needs approval).
- [x] **M2.4 Plain-language report.**
  - Depends on: M2.3.
  - Goal: `report.md` that a novice can read.
  - Files: `src/access_review/report.py`, `tests/test_report.py`, `tests/golden/`.
  - Content per finding: what is wrong in one sentence, who can do it, the proof (the exact statement and what came back), and a fix as text the developer can give to their own AI. When no finding: the exact sentence "No violation found under this test." The tool never changes the developer's code.
  - Validation: golden-file test for each planted app. A jargon test: terms such as "RLS", "policy", "anon", "JWT" must be explained in plain words the first time they appear in a report. A test asserts the word "secure" never appears except inside "No violation found under this test."
- [x] **M2.5 Command line.**
  - Depends on: M2.4.
  - Goal: `python -m access_review review <migrations_dir> --out report.md`.
  - Files: `src/access_review/cli.py`, `tests/test_cli.py`.
  - Validation: on `rows-01` vulnerable, exit code 1 and a report with one finding. On the fixed twin, exit code 0 and the "No violation" sentence. On a broken migration, exit code 2 and the reason (M1.7).
- [x] **G2 (owner).** Maneet runs the command on the vulnerable and the fixed twin, and reads both reports. Is the vulnerable report understandable to a classmate who has never heard of row security? Maneet signs off or lists what to reword.

### M3 More attacks

All M3 tasks depend on G2. M3.1 to M3.8 can be done in any order. M3.9 depends on all of them.

Pattern for every task below: add the probe, add a planted vulnerable and fixed pair using the flaw ids in Appendix A, add the key entries, and add a negative control. Each new probe returns Evidence (M2.1) and each new rule returns a Finding (M2.2).

- [x] **M3.1 Insert as a visitor and as a user with someone else's owner id (R3, R4).** Apps: `writes-01-visitor-insert`, `writes-02-spoofed-owner`. Validation: the vulnerable apps accept the insert, the fixed ones refuse it. All writes run inside a transaction that is rolled back.
- [x] **M3.2 Update and delete another user's row (R5, R6).** Apps: `writes-03-update-others`, `writes-04-delete-others`. Same validation.
- [x] **M3.3 Take over a row by changing its owner (R7).** App: `writes-05-owner-change`, missing check on new values. Validation: after the update the row belongs to the attacker (assert).
- [x] **M3.4 Protected column is writable by the user (C1).** Apps: `columns-01-self-admin` (a user sets their own `role` or `is_admin`), `columns-02-self-paid`. The probe updates a protected column on the actor's own row. Which columns count as protected comes from names like `role`, `is_admin`, `balance`, `paid`, `owner_id`, and from the key. If unsure, status `needs_decision`.
- [x] **M3.5 Private column is readable by others (C2).** App: `columns-03-phone-exposed`, a public profile table that also exposes phone numbers. Probe: read a private-looking column as another user or visitor.
- [x] **M3.6 A view that bypasses row security (V1).** App: `views-01-bypass`. A view created without the caller's rights shows everyone's rows even though the table underneath is locked. Validation: vulnerable view leaks, fixed view does not. Read the Supabase page on views in full and cite it in the PR.
- [x] **M3.7 Functions: a signed-in user or visitor can call something they should not (U1, U2, U3).** Apps: `functions-01-admin-delete-any-user`, `functions-02-security-definer-no-check`, `functions-03-default-execute`. Probe: call each function with typed dummy arguments inside a savepoint that is rolled back, and record success, permission denied or other error. Status is `proved` only when the call actually ran.
- [x] **M3.8 Decoys and clean apps.** Apps: `decoy-02-public-profile-read` (public on purpose), `decoy-03-shared-team-table`, `clean-01-all-correct`, `clean-02-all-correct-different-style`. Validation: zero `proved` findings on clean apps. Decoys never give `proved`. This is the false-alarm test. Result: `decoy-02` gives R1 `needs_decision` (a visitor reads a table with no owner column). `decoy-03` gives no finding at all, because visitors are refused and there is nothing to ask (see `ASSUMPTIONS.md`, M3.8).
- [x] **M3.9 The tests must have teeth.**
  - Depends on: M3.1 to M3.8.
  - Goal: prove the tests can fail.
  - Files: `tests/test_teeth.py`.
  - Steps: for each probe, a test swaps it for a broken version (always returns nothing, or always returns everything) and asserts the planted-app tests fail.
  - Validation: `pytest tests/test_teeth.py` passes, meaning every broken probe is caught.
- [x] **G3 (owner).** Ticked on owner's instruction. Maneet runs the command on any three planted apps from different groups and reads the reports. Then Maneet reads `planted/answer_key.json` for one app and checks it agrees with Appendix A.

### M4 Evaluation protocol frozen

Why before scoring: if the answer key or the rules change after seeing results, the results mean nothing.

- [x] **M4.1 Write `docs/EVALUATION.md`.**
  - Depends on: G3.
  - Contents: definitions of recall (planted flaws found / planted flaws), precision (findings that match a planted flaw / all proved findings), false alarm (proved findings on fixed twins, clean apps and decoys). The matching rule (same app, same flaw id, same table or column or function). How `needs_decision` is counted (reported separately, never as a finding). What counts as a successful fix (M6). No target numbers are promised.
  - Needs Maneet's approval.
- [x] **M4.2 Scoring module.**
  - Depends on: M4.1.
  - Files: `src/access_review/scoring.py`, `tests/test_scoring.py`. It reads findings JSON and the answer key only. It must not import probes, rules or the sandbox (a test checks the imports).
  - Validation: hand-written findings give hand-computed recall, precision and false alarms. Negative control: dropping one finding lowers recall by the expected amount.
- [x] **M4.3 Dev-set run.**
  - Depends on: M4.2.
  - Goal: `python -m access_review.scoring planted/` prints a score table for our own tool on the dev set. Expected on the dev set: every planted flaw found and zero false alarms, since we built the dev set alongside the tool. This is a self-check, not a result. It is never quoted as accuracy.
- [x] **M4.4 DECISION D3 and the held-out set.**
  - Goal: apps the tool's author never saw.
  - Process: a fresh session is given only Appendix A and the answer key shape, and writes pairs in a different style (other table names, other policy styles, other schema layouts), including decoys and clean apps. The files go in `heldout/`, which is not read by the coding agent until M5.4.
  - Validation: the held-out files validate against the key shape. Maneet reviews the key.
- [x] **M4.5 Freeze.**
  - Goal: tag the repo `eval-freeze-1` once G4 is signed. After the tag: no changes to probes, rules or the key without a DECISION, and any such change means the held-out set must be rewritten and rerun.
- [x] **G4 (owner).** Ticked on owner's instruction. Maneet reads `docs/EVALUATION.md`, confirms it, and creates the tag.

### M5 Compare with other tools

M5 runs other tools on the same apps and scores every tool with the frozen rules in `docs/EVALUATION.md`. Rules for the whole milestone:

- Tasks run in order, one PR each. M5.1, M5.2 and M5.3 must never open `heldout/`: no reading, listing, copying or searching inside it, by hand or by script. Only the held-out run in M5.4 may open it.
- Only one task at a time uses Docker. M5.2 and M5.4 use it, and so does any run of the full test suite. Run `docker ps -a` first; it must show no sandbox container.
- Baselines are scored with the same rules as our tool, through adapters. `docs/EVALUATION.md`, `planted/answer_key.json` and `heldout/` are not changed. A change to any of them is its own PR and needs Maneet's approval (rule 12).
- No tool is tuned to the dev set or to the held-out set. No baseline rule or option is written or edited to fit one planted app. If a baseline has nothing for a kind of flaw, it finds nothing there, and that is the result.
- Files for M5 live in these places: `docs/baselines.md` (choice, commands, mapping rules), `src/access_review/adapters/` (one module per baseline), `scripts/run_baselines.py`, `tests/fixtures/baselines/` (sample outputs), `results/` (raw outputs and score tables), `docs/results.md` (the table for the report).

- [x] **M5.1 DECISION D4: choose the baselines.**
  - Depends on: G4.
  - Goal: a written choice of baseline tools, with the reason for each one, committed before any baseline is run.
  - Files: create `docs/baselines.md` (section "1. Choice"); add one entry to `ASSUMPTIONS.md`. Do not touch: `src/`, `planted/`, `heldout/`, `docs/EVALUATION.md`, `results/`. Never open `heldout/`.
  - Steps:
    1. Read each candidate's pages in full (rule 11): Semgrep, the Supabase advisors, rlsautotest, pgrls, rlsgrid, SupaShield. At least the project page, the licence, the install page and the page on how to run it. Quote at most one line per page.
    2. For each tool record: version, licence, install route, whether a run needs a network or an account once installed, whether it runs locally, which flaw ids from Appendix A it could report, and whether it runs statements against a database (execution-based) or only reads files (static).
    3. Drop any tool that needs a network or an account to run, or that costs money. Say why in the file and name the page that says so.
    4. The set must include Semgrep, the Supabase advisors and at least one execution-based database tool. Add other tools only if they pass step 3.
    5. Write one table row per candidate: tool, version, licence, how it runs, offline (yes or no), covers, kind, decision (`Included` or `Dropped`), reason.
    6. Log the decision in `ASSUMPTIONS.md` (date, options seen, picks, why), then tick M5.1 and update section 1.
  - Validation:
    - `ruff check .` passes.
    - `grep -c -i -E "^\| *(Semgrep|Supabase advisors|rlsautotest|pgrls|rlsgrid|SupaShield) *\|" docs/baselines.md` prints 6. Assertion: every candidate has one row with a decision and a reason.
    - `grep -c -E "\| *Included *\|" docs/baselines.md` prints 3 or more, and the Semgrep and Supabase advisors rows say `Included`. Assertion: the required set is present.
    - `git ls-files results | grep -c heldout` prints 0. Assertion: no held-out run exists yet.
    - `git diff --name-only origin/main` lists only `docs/baselines.md`, `ASSUMPTIONS.md` and `docs/ROADMAP.md`.
  - Done when: `docs/baselines.md` is merged, so the choice exists on `main` before the held-out run. After that run it cannot change (M5.5).
  - Stop and ask if: Semgrep or the Supabase advisors cannot meet the free, local, no-network rule (the D4 wording would then need to change); no execution-based database tool qualifies; a licence is unclear.
- [x] **M5.2 Exact commands per baseline, and the mapping rules.**
  - Depends on: M5.1.
  - Goal: for every included baseline, the exact command that runs it on a rebuilt planted app with no network, and written rules that turn its output into a findings item with a flaw id and a table, column or function.
  - Files: `docs/baselines.md` (add sections "2. Commands" and "3. Mapping rules"); `tests/fixtures/baselines/<tool>/` (raw outputs from dev apps); `baselines/<tool>/` (pinned config or published rule files, only if a tool needs them); `ASSUMPTIONS.md`. Do not touch: `src/`, `planted/`, `heldout/`, `docs/EVALUATION.md`. Never open `heldout/`. This task uses Docker.
  - Steps:
    1. Read each included tool's run page again in full (rule 11).
    2. For each tool, pick dev apps from `planted/` that cover the flaw groups the tool can report, and use both the vulnerable and the fixed side. Rebuild each with the sandbox (`python -m access_review.demo_sandbox` shows how) so execution-based tools have a database to attack.
    3. Write the exact command per tool: working folder, flags, tool version, how it is pointed at the migration files or at the rebuilt database, how the network is off (for example a container with no network), output format and where the output goes. Run it. Save the raw output of both sides under `tests/fixtures/baselines/<tool>/`.
    4. Use published rules and built-in checks only. No rule or option is written or edited to fit a planted app. Pin the rule source and version.
    5. Write the mapping rules. For each tool, a table: tool rule or check id, flaw id (Appendix A), where the table, column or function name is read in the output, and any condition. An item the rules cannot place in a flaw id and a target is not emitted; it is counted as unmapped and stays in the raw output. The rules come from the tool's own documentation and from `planted/` only. They are written before M5.4 and are never derived from `heldout/`.
    6. Decision, confirmed by Maneet in PR 66: every mapped baseline finding is emitted with status `proved`, because the scorer counts only `proved`. The results table labels baselines "reported, not executed" and our tool "executed". `docs/EVALUATION.md` is not changed.
    7. Log the choices in `ASSUMPTIONS.md`, then tick M5.2 and update section 1.
  - Validation:
    - `ruff check .` passes.
    - For each included tool, run the command from `docs/baselines.md` word for word on the vulnerable and the fixed side of the chosen dev app. Assertion: the findings equal the saved fixture, and the command works with the network off (say how this was checked).
    - Negative control: the tool reports at least one item on the vulnerable side and none on the fixed side. If a tool reports nothing on either side, the file says so in plain words and the reason.
    - `docker ps -a` shows no leftover sandbox container.
    - `grep -rn heldout docs/baselines.md baselines tests/fixtures/baselines` prints nothing.
    - `git diff --name-only origin/main` lists only the files named above.
  - Done when: every included tool has a command that was run, saved sample outputs and a mapping table, and the mapping rules state the `proved` rule.
  - Stop and ask if: a tool needs a network or an account at run time; the mapping can only work by changing `docs/EVALUATION.md` or the key; Maneet later withdraws the `proved` rule (a different rule is a change to `docs/EVALUATION.md`, in its own PR).
- [x] **M5.3 One adapter per baseline, and the runner.**
  - Depends on: M5.2.
  - Goal: each baseline's raw output becomes the run object the scorer reads, and one script runs a baseline over a folder of apps.
  - Files: create `src/access_review/adapters/` (one module per included baseline), `scripts/run_baselines.py`, `tests/test_adapters.py`, more samples under `tests/fixtures/baselines/`. `docs/baselines.md` only to correct a mapping rule the adapter shows to be ambiguous; say so in the PR. Do not touch: `scoring.py`, `probes.py`, `rules.py`, `sandbox.py`, `planted/`, `heldout/`, `docs/EVALUATION.md`. Never open `heldout/`.
  - Steps:
    1. Read `scripts/run_devset.py`, `src/access_review/findings.py` and `schemas/finding.schema.json`. An adapter takes the raw output text plus the app and side, and returns the same run object `run_devset.py` writes: `app`, `side`, `not_checkable`, `probe_errors`, `findings`, `notes`.
    2. Each finding follows the mapping rules in `docs/baselines.md`, has status `proved` (M5.2), and keeps the raw output line as its proof. Unmapped items are not emitted; their count goes in `notes`.
    3. Output that cannot be read (tool crash, non-zero exit, unparseable text) gives `not_checkable: true` with the reason in `notes`. It never gives an empty result that looks clean.
    4. `scripts/run_baselines.py <folder> --tool NAME --out DIR` runs the command from `docs/baselines.md` on each scored folder (use `expected_runs` from `scoring.py`), saves the raw output in `DIR/raw/` and the run object in `DIR/<app>__<side>.json`. It is not run on a full set in this task.
    5. Tests use only the saved samples and hand-written ones. No test opens `heldout/`.
    6. Tick M5.3 and update section 1.
  - Validation:
    - `pytest tests/test_adapters.py -v` passes. Assertions: the vulnerable sample gives exactly the hand-written expected findings (flaw id and target); a schema check accepts every finding; an unmapped item emits nothing and is counted; garbage input gives `not_checkable`; adapter output scored with `access_review.scoring.score` gives the hand-computed recall.
    - Negative control: the fixed-side sample (or an empty output) gives no findings, and dropping the one finding lowers recall from 1 of 1 to 0 of 1.
    - `grep -rn heldout src/access_review/adapters scripts/run_baselines.py tests/test_adapters.py` prints nothing.
    - `pytest tests/test_scoring.py -v` still passes (scoring still imports nothing from probes, rules or the sandbox).
    - `python scripts/check.py` prints ALL PASS. Run it once, alone: it uses Docker.
  - Done when: every included baseline has an adapter with a passing test and a negative control, and the runner exists.
  - Stop and ask if: a baseline's output cannot be mapped without guessing intent; the finding shape cannot hold the baseline's evidence without a change to `findings.py` or the schema.
- [x] **M5.4 Run every tool on the dev set, then once on the held-out set.**
  - Depends on: M5.3.
  - Goal: raw outputs and score tables for our tool and every baseline, on the dev set and on the held-out set, with the held-out run done once.
  - Files: create `results/baselines/devset/<tool>/`, `results/baselines/heldout/<tool>/`, `results/heldout/` (our tool, same layout as `results/devset/`), `results/heldout/RUN.txt`, and the score tables. Bug fixes in `scripts/run_baselines.py` and `src/access_review/adapters/` found in the dev run only. `src/access_review/scoring.py` only if the check in step 5 needs a tiny change that alters no rule. Do not touch: `probes.py`, `rules.py`, `sandbox.py`, `baseline.sql`, `planted/`, `heldout/` files, `docs/baselines.md`, `docs/EVALUATION.md`. This task uses Docker.
  - Rule: nothing is tuned after the held-out run (see M5.5). If a mistake in a command or a mapping rule shows up in the dev run, fix it in its own docs PR, merged before the held-out run.
  - Steps:
    1. Run `docker ps -a`; no sandbox container may be listed. Check the tag: `git rev-parse eval-freeze-1` prints `1080063...`.
    2. Dev set, our tool: reuse `results/devset/` if no frozen file changed since the tag (the check is in Validation). Do not re-tune.
    3. Dev set, each baseline: `python scripts/run_baselines.py planted/ --tool NAME --out results/baselines/devset/NAME`, then `python -m access_review.scoring planted/ --runs results/baselines/devset/NAME` and save the table to `results/baselines/devset/score-NAME.txt`. Fix adapter or runner bugs found here.
    4. Check that the scorer accepts the held-out set. Read `expected_runs` and `load_key` in `scoring.py` (they take a folder that holds `answer_key.json`). Then run `python -m access_review.scoring heldout/ --runs <empty folder>`: it must list missing runs and exit 2, with no error about the folder or the key. This is the first time `heldout/` is opened and no tool has run on it. Any change to scoring code must be tiny, change no rule, and keep `scoring.py` importing nothing from probes, rules or the sandbox.
    5. Freeze: commit everything, make `git status --short` print nothing, then write `results/heldout/RUN.txt` with `git rev-parse HEAD` and every tool's version. No file under `results/heldout/` or `results/baselines/heldout/` exists before this point.
    6. Held-out run, once, every tool, one at a time: `python scripts/run_devset.py heldout/ --out results/heldout` for our tool, and `python scripts/run_baselines.py heldout/ --tool NAME --out results/baselines/heldout/NAME` for each baseline. Save each raw output as soon as it is made.
    7. Crash rule, confirmed by Maneet in PR 66: a tool crash or an adapter bug in the held-out run may be fixed and that run repeated only if the fix does not change which findings count, shown by an empty diff of the saved run objects of every run that did not crash, and no change to a mapping rule or a tool option. Otherwise the run stays as a not-checkable miss (`not_checkable: true`, no findings) and is not repeated. A sandbox build failure of our own tool is a not-checkable miss and is not repeated.
    8. Score every tool with `python -m access_review.scoring heldout/ --runs <dir>` and save each table next to its raw outputs. The `needs_decision` count is printed by the scorer; do not cut it from any saved table.
    9. Do not tune after step 6. If a fixed twin gives a finding, or a result looks like an author error in the held-out set, report it in the PR and change nothing. Replacing the held-out set is Maneet's decision.
    10. Log in `ASSUMPTIONS.md`, then tick M5.4 and update section 1.
  - Validation:
    - `git diff --name-only eval-freeze-1 -- src/access_review/probes.py src/access_review/rules.py src/access_review/sandbox.py src/access_review/baseline.sql planted heldout docs/EVALUATION.md` prints nothing. Assertion: nothing frozen changed.
    - `python -m access_review.scoring planted/` output equals `results/devset-score.txt` (ignore line endings). Assertion: our dev self-check is unchanged.
    - Negative control: `python -m access_review.scoring planted/ --runs <empty folder>` exits 2.
    - `pytest tests/test_scoring.py -v` passes.
    - For each tool, the number of run files under its held-out folder equals the number under `results/heldout/`. Assertion: no run was dropped.
    - `git merge-base --is-ancestor <hash in RUN.txt> HEAD` exits 0.
    - `python scripts/check.py` prints ALL PASS, run once and alone after the Docker runs finish.
    - `docker ps -a` shows no leftover sandbox container.
  - Done when: every tool has saved raw outputs and a score table for both sets, `RUN.txt` records the commit used, and the PR names every not-checkable run and every crash.
  - Stop and ask if: the held-out key or folder layout is not accepted by the scorer and the fix is more than tiny; the held-out run would need a rule, probe, key or mapping change; Docker does not start; a tool needs a network at run time.
- [x] **M5.5 Check that nothing was tuned after the held-out run.**
  - Depends on: M5.4.
  - Goal: a command that fails if any frozen file changed after the held-out run, so the no-tuning rule can be checked and not only stated. If it must fail for a real reason, the held-out set is replaced (Maneet decides, by D3 and a new freeze tag).
  - Files: create `scripts/check_no_tuning.py`, `tests/test_check_no_tuning.py`. Do not touch: `results/`, `src/`, `planted/`, `heldout/`, `docs/EVALUATION.md`, `docs/baselines.md`.
  - Steps:
    1. The script reads the commit in `results/heldout/RUN.txt` and runs git against it. It fails if any of these changed after that commit: `src/access_review/`, `planted/`, `heldout/`, `docs/EVALUATION.md`, `docs/baselines.md`, `scripts/run_devset.py`, `scripts/run_baselines.py`, `tests/test_adapters.py`, `tests/fixtures/baselines/`. It also fails if a file under `results/heldout/` or `results/baselines/heldout/` was modified or deleted (added files are allowed). It prints each offending path.
    2. The test builds a small temporary git repo, so it needs no Docker and no network. Negative control: edit one frozen file after the recorded commit and the script exits 1; with no edit it exits 0.
    3. Tick M5.5 and update section 1. The script is not added to CI (a shallow clone has no history).
  - Validation:
    - `pytest tests/test_check_no_tuning.py -v` passes, including the negative control.
    - `python scripts/check_no_tuning.py` exits 0 on the real repo and prints the commit it checked against.
    - `ruff check .` passes.
  - Done when: the script passes on `main` after the PR, and the rule is written in M5.4 and here.
  - Stop and ask if: the script fails on the real repo (do not change the frozen file back by hand: report which path changed and why).
- [x] **M5.6 Results table for the report.**
  - Depends on: M5.5.
  - Goal: one results page where every score has its `needs_decision` count beside it, and the dev set and the held-out set are never merged.
  - Files: create `docs/results.md`, `tests/test_results_table.py`. Do not touch: `scoring.py`, `results/` raw files, `docs/EVALUATION.md`, `planted/answer_key.json`.
  - Steps:
    1. Two separate tables: held-out set first, dev set second. No total, no average, no pooled row across the two.
    2. One row per tool. Columns: tool, kind ("executed" for our tool, "reported, not executed" for baselines), recall as counts then ratio, precision as counts then ratio, false alarms (count and rate), extra findings (named), not checkable, probe errors, `needs_decision` count. Counts first, ratio second; a zero denominator prints `n/a`.
    3. A line under the dev table: it is a self-check, never quoted as accuracy. A line under both: the limits in `docs/EVALUATION.md` section 8, and the `proved` rule for baselines (M5.2).
    4. Wording: "No violation found under this test." Never "secure". No target numbers.
    5. A short "How to check by hand" section: for any app, the paths of the raw output, the run object and the key entry, so G5 can be done.
    6. Tick M5.6 and update section 1.
  - Validation:
    - `pytest tests/test_results_table.py -v` passes. It re-scores the saved runs with `access_review.scoring.score` and asserts every number in the tables equals the re-scored value, and that every table row has a `needs_decision` count.
    - Negative control: the test, run on a copy of the page with one number changed, fails.
    - `grep -n -i secure docs/results.md` prints nothing.
    - `ruff check .` passes.
  - Done when: `docs/results.md` is merged and its test passes in CI.
  - Stop and ask if: a number cannot be reproduced from the saved raw outputs; a table would need the two sets combined.
- [x] **G5 (owner).** Signed off by Maneet on 2026-11-20.
  - Depends on: M5.6.
  - Maneet checks the table against the raw outputs for two apps by hand: pick two apps, and for each tool open the raw output, the run object and the key entry named in the "How to check by hand" section of `docs/results.md`. Each reported finding traces to a raw output line and to a mapping rule, and each count in the table follows. Maneet signs off or lists what to fix.
  - Recorded: Maneet opened the key entry, our tool's run object and the raw outputs for `orbit-tasks` and `pantry-share` (fixed side) for our tool, the Supabase advisors and Semgrep. The rlsautotest and pgrls files for the same two apps were read and summarised for Maneet, who then signed off. Everything matched the table in `docs/results.md`. One pgrls rule that produced R1 on `pantry-share/fixed` was not traced.

### M6 Fix check

M6 tests the fix step: after a flaw is reported, does a fix remove the flaw without breaking the app. What counts as a successful fix is fixed in `docs/EVALUATION.md` section 6, and this milestone does not change it. Rules for the whole milestone:

- Tasks run in order, one PR each. Nothing in M6 opens `heldout/`: no reading, listing, copying or searching inside it. The held-out set is spent. It is not run, not tuned on and not used for fixes.
- Only one task at a time uses Docker. M6.2, M6.3, M6.5, M6.6 and M6.8 use it, and so does any run of the full test suite. Run `docker ps -a` first; it must show no sandbox container. Run `python scripts/check.py` alone, in the background, and wait for it.
- A fix is a new migration file added to a copy of the vulnerable app. The tool never edits the developer's files, and the copy is made outside `planted/`.
- No-edit rule: M6 never changes `planted/answer_key.json`, `src/access_review/` (probes, rules, sandbox, scoring, baseline.sql, adapters, everything), `planted/`, `heldout/`, `docs/EVALUATION.md`, `docs/baselines.md`, `scripts/run_devset.py`, `scripts/run_baselines.py` or the saved files under `results/` that already exist. M6 code lives in a new package `src/fix_check/` and imports `access_review` without editing it. This keeps `scripts/check_no_tuning.py` passing, because it fails on any change under `src/access_review/`. If a task seems to need a change to a frozen file, stop and ask (rule 12). `python scripts/check_no_tuning.py` must still exit 0 after every task.
- Every attempt is recorded, including failures and attempts that gave no usable fix. The number of attempts is written in `docs/fixcheck-plan.md` (M6.1) and merged before the first run. No attempt is dropped or repeated to get a better number.
- Fix sources are reported separately: the reference fixed twin, and an AI that sees only the report's fix text (D5). Their numbers are never added together.
- The dev-set result is a self-check. It is never quoted as accuracy, and the wording is "No violation found under this test." Never "secure".
- Files for M6 live in these places: `docs/fixcheck-plan.md`, `src/fix_check/`, `tests/test_fix_check_*.py`, `tests/fixtures/fixcheck/`, `fixes/reference/` (one fix file per app), `fixes/ai/` (one folder per AI attempt), `results/fixcheck/` (one run object per attempt, and score tables), `docs/fixcheck-results.md`.

- [x] **M6.1 Write the plan before any run.**
  - Depends on: G5.
  - Goal: a committed plan that fixes the number of attempts, the AI and the prompt before any fix is run, so the numbers cannot be shaped afterwards.
  - Files: create `docs/fixcheck-plan.md`; add entries to `ASSUMPTIONS.md`. Do not touch: `src/`, `planted/`, `heldout/`, `docs/EVALUATION.md`, `results/`. Never open `heldout/`. No Docker.
  - Steps:
    1. Read `docs/EVALUATION.md` section 6 and `planted/answer_key.json` (keys only, not the app folders). List the apps that have both a `vulnerable/` and a `fixed/` folder and at least one planted flaw. These are the apps in the fix check. Apps with no planted flaw (decoys, clean apps, `rows-03-locked-out`) and `hostile-01-callout` are out, because there is nothing to fix.
    2. Write the attempt counts: reference source, one attempt per app. AI source, three independent attempts per app, no retry after a failure and no feedback from one attempt to the next. Write the totals for both.
    3. Write which AI and which prompt is used, and say that the prompt is fixed text saved in the plan. The AI sees only the fix text from the tool's report for the vulnerable app (what a developer would paste into their own AI). It never sees the code, the key, the fixed twin or any score. Write how the answer is turned into one SQL file, and that an empty or unusable answer is an attempt that fails condition 1.
    4. Write the four conditions of `docs/EVALUATION.md` section 6 in plain words, how each failed attempt is labelled by the conditions it broke, and the table that M6.9 will print.
    5. Write what is out of scope: `heldout/` is not used; no tuning of fixes, prompts or tools after seeing a result; real public apps are not fixed or scored.
    6. Log every default you chose in `ASSUMPTIONS.md`, one line each, then tick M6.1 and update section 1.
  - Validation:
    - `ruff check .` passes.
    - The attempt counts in the plan equal what the key gives: a one-line script counts the apps from step 1 and prints the same number as the plan. Assertion: the totals are not guessed.
    - `grep -n -i -E "secure|heldout/" docs/fixcheck-plan.md` prints nothing except the sentence that says `heldout/` is not used. Assertion: the plan names no held-out content.
    - `git diff --name-only origin/main` lists only `docs/fixcheck-plan.md`, `ASSUMPTIONS.md` and `docs/ROADMAP.md`.
  - Done when: `docs/fixcheck-plan.md` is merged. After the first fix run it cannot change (M6.8).
  - Stop and ask if: the plan would need a paid service or a new account; the plan would need `docs/EVALUATION.md` or the key to change.
- [ ] **M6.2 Allowed-list check, read entries.**
  - Depends on: M6.1.
  - Goal: a function that says whether the allowed entries of an app that are about reading still hold on a rebuilt app (condition 3 for reads).
  - Files: create `src/fix_check/__init__.py`, `src/fix_check/allowed.py`, `tests/test_fix_check_allowed.py`. Do not touch: `src/access_review/`, `planted/`, `heldout/`, `docs/EVALUATION.md`. Never open `heldout/`. This task uses Docker.
  - Steps:
    1. Read `src/access_review/probes.py`, `tests/test_planted.py` (`test_allowed_access_survives_in_the_fixed_twin`) and the `allowed` entries of the key. The read entries are: `read` with `own_row_only`, `public` or `team_rows_visible`; `read_view` with `own_row_visible`; `read_column` with `public_columns_readable`.
    2. Write `check_allowed(box, app, key)` for those entries, using existing probes only. It returns one item per entry: the entry, `holds` true or false, and the evidence. An entry with `expected_failure` is returned with that field and is not counted when the caller decides condition 3 (`docs/EVALUATION.md` section 6).
    3. An entry it cannot check (an `expect` value it has no rule for) is returned as `holds: false` with the reason `not_checkable`. It is never skipped, so it cannot look like a pass.
    4. Tick M6.2 and update section 1.
  - Validation:
    - `pytest tests/test_fix_check_allowed.py -v` passes. Assertions: on every fixed twin that has a read entry, every entry without `expected_failure` holds; on `rows-03-locked-out/fixed` the `own_row_only` entry does not hold and carries `locks_out_owner` (negative control).
    - Negative control: a fixture app under `tests/fixtures/fixcheck/` with a policy that hides every row from a signed-in owner makes a `read` entry not hold.
    - An unknown `expect` value gives `holds: false` and `not_checkable`.
    - `python scripts/check_no_tuning.py` exits 0. `ruff check .` passes. `docker ps -a` shows no leftover sandbox container.
  - Done when: every read entry of the key has a rule and a passing test, with a negative control.
  - Stop and ask if: checking an entry needs a new probe or a change to `probes.py`.
- [ ] **M6.3 Allowed-list check, write and call entries.**
  - Depends on: M6.2.
  - Goal: the same function covers the allowed entries about changing data and calling functions (condition 3 for writes and calls).
  - Files: `src/fix_check/allowed.py`, `tests/test_fix_check_allowed.py`, more fixtures under `tests/fixtures/fixcheck/`. Do not touch: `src/access_review/`, `planted/`, `heldout/`, `docs/EVALUATION.md`. Never open `heldout/`. This task uses Docker.
  - Steps:
    1. The write and call entries are: `update` with `own_row_changed`; `insert` with `own_owner_accepted`; `delete` with `own_row_deleted`; `call` with `call_runs`, `own_note_changed` or `own_rows_only`.
    2. Extend `check_allowed` for them, using existing probes only. Every write runs inside a transaction that is rolled back, as in M3.1.
    3. Keep step 3 of M6.2: an entry with no rule is `holds: false`, `not_checkable`.
    4. Tick M6.3 and update section 1.
  - Validation:
    - `pytest tests/test_fix_check_allowed.py -v` passes. Assertion: on every fixed twin, every entry without `expected_failure` holds, for all 20 entries of the two tasks together.
    - Negative control: for each of `update`, `insert`, `delete` and `call`, a fixture app that blocks the owner's own action makes that entry not hold.
    - After a check, the database holds the same rows as before it (assert a row count), so the check changes nothing.
    - `python scripts/check_no_tuning.py` exits 0. `ruff check .` passes. `docker ps -a` shows no leftover sandbox container.
  - Done when: every `expect` value in the key has a rule, a passing test and a negative control.
  - Stop and ask if: an entry cannot be checked with the existing probes.
- [ ] **M6.4 Build a fix attempt.**
  - Depends on: M6.1.
  - Goal: from a vulnerable app folder and one SQL file, build a copy with the fix added as a new migration, and never touch the original.
  - Files: create `src/fix_check/attempt.py`, `tests/test_fix_check_attempt.py`. Do not touch: `src/access_review/`, `planted/`, `heldout/`, `docs/EVALUATION.md`. Never open `heldout/`. No Docker.
  - Steps:
    1. Read how `src/access_review/sandbox.py` orders and applies migration files, and how `planted/` names them.
    2. Write `build_attempt(vulnerable_migrations, fix_sql, workdir)`: copy the migrations to `workdir`, add the fix as one new file that is applied last, return the folder. An empty fix, a fix that is not text, or a fix that is not a single file is refused with a plain reason.
    3. The original folder is read only. A test hashes it before and after.
    4. Tick M6.4 and update section 1.
  - Validation:
    - `pytest tests/test_fix_check_attempt.py -v` passes. Assertions: the copy holds every original file unchanged plus one new file that sorts last; the original folder hash is equal before and after; an empty fix is refused.
    - Negative control: a fix file named so that it sorts before the originals is renamed or refused, not applied first.
    - `python scripts/check_no_tuning.py` exits 0. `ruff check .` passes.
  - Done when: the builder exists with a passing test and the no-edit assertion.
  - Stop and ask if: the sandbox's file ordering cannot guarantee that the fix applies last.
- [ ] **M6.5 The `recheck` command.**
  - Depends on: M6.3, M6.4.
  - Goal: `python -m fix_check recheck <app> <fix.sql>` rebuilds the vulnerable app with the fix and reports the four conditions of `docs/EVALUATION.md` section 6, each PASS or FAIL.
  - Files: create `src/fix_check/recheck.py`, `src/fix_check/__main__.py`, `tests/test_fix_check_recheck.py`, fixtures under `tests/fixtures/fixcheck/`. Do not touch: `src/access_review/`, `planted/`, `heldout/`, `docs/EVALUATION.md`, `scripts/run_devset.py`. Never open `heldout/`. This task uses Docker.
  - Steps:
    1. Read `docs/EVALUATION.md` section 6, `src/access_review/cli.py` (`review`), `src/access_review/scoring.py` and `scripts/run_devset.py` (`run_folder`).
    2. Condition 1: the attempt folder (M6.4) builds. A `NotCheckable` result fails it and the reason is printed; conditions 2 to 4 are then reported as not run, never as pass.
    3. Condition 2: review the attempt folder; it fails if any proved finding matches a planted flaw of the app. Use the matching rule in `scoring.py` (section 3 of `docs/EVALUATION.md`); do not write a second copy of it.
    4. Condition 3: `check_allowed` (M6.2, M6.3). It fails if any entry without `expected_failure` does not hold. An empty `allowed` list passes vacuously and the output says so.
    5. Condition 4: review the original vulnerable folder in the same command, and fail if the attempt has a proved finding whose flaw id and target are absent from the vulnerable review.
    6. Output: one line per condition, then `fix works` or `fix does not work`, then the run object (the four results, the broken conditions, the notes). Exit 0 if all four pass, 1 if any fails, 2 if the check cannot run. The command never writes into the app folder.
    7. Tick M6.5 and update section 1.
  - Validation:
    - `pytest tests/test_fix_check_recheck.py -v` passes. Assertion: the fixed twin's change, written as a fix file for `rows-01-profiles`, passes all four conditions and exits 0.
    - Negative control, lock-out: a fix that locks everyone out of the table (`USING (false)`) fails condition 3 and passes condition 2. This is the case named in `docs/EVALUATION.md` section 6.
    - Negative control, wrong table: a fix that closes a different table fails condition 2.
    - Negative control, new leak: a fix that opens a second table to visitors fails condition 4.
    - Negative control, broken fix: a fix with a syntax error fails condition 1 and reports conditions 2 to 4 as not run.
    - The original folder hash is equal before and after every run.
    - `python scripts/check_no_tuning.py` exits 0. `ruff check .` passes. `docker ps -a` shows no leftover sandbox container. `python scripts/check.py` prints ALL PASS: run it once, alone, in the background.
  - Done when: the command exists, and all four negative controls fail the condition they should and no other.
  - Stop and ask if: a condition cannot be decided without a change to `scoring.py`, `rules.py`, `probes.py` or the key.
- [ ] **M6.6 Reference fixes and a runner.**
  - Depends on: M6.5.
  - Goal: for every app in the fix check, a fix file taken from the reference fixed twin, and one command that runs all of them and records each attempt.
  - Files: create `fixes/reference/<app>.sql` (one per app), `src/fix_check/run.py`, `tests/test_fix_check_run.py`. Do not touch: `src/access_review/`, `planted/`, `heldout/`, `docs/EVALUATION.md`, `docs/fixcheck-plan.md`, `results/`. Never open `heldout/`. This task uses Docker.
  - Steps:
    1. For each app in `docs/fixcheck-plan.md`, compare its `vulnerable/` and `fixed/` migration files and write the difference as one new SQL file that, applied after the vulnerable files, gives the fixed twin's behaviour (drop or replace the policy, the grant, the view or the function). Use only the two folders of that app. Do not write a fix to pass the checks: write the twin's change.
    2. Write `python -m fix_check run reference --out DIR`. For every fix file it runs `recheck` and saves one run object `DIR/<app>__<n>.json` with the fix file name, the four results and the broken conditions. It prints one line per attempt and the totals. One run at a time, because each uses Docker.
    3. Run it once on the dev set into a scratch folder (not `results/`). An app whose fix does not pass is kept as it is and listed in the PR: the reference twin is not corrected to look better. Say why in the PR.
    4. Tick M6.6 and update section 1.
  - Validation:
    - `pytest tests/test_fix_check_run.py -v` passes. Assertions: the runner counts as many attempts as the plan says; a missing fix file is an attempt that fails condition 1 and is counted, not skipped.
    - Run the command on the dev set and paste the totals line. Assertion: the attempts equal the plan's reference total.
    - Negative control: replace one fix file in a scratch copy by a lock-out fix; the totals show one more failure and name condition 3.
    - `grep -rn heldout fixes src/fix_check tests/test_fix_check_run.py` prints nothing.
    - `python scripts/check_no_tuning.py` exits 0. `ruff check .` passes. `docker ps -a` shows no leftover sandbox container.
  - Done when: every app in the plan has a reference fix file and the runner reports the totals.
  - Stop and ask if: a twin differs from the vulnerable side in a way one added migration cannot express.
- [ ] **M6.7 The AI fix source.**
  - Depends on: M6.6.
  - Goal: a command that gives an AI only the report's fix text, saves everything it said, and turns its answer into a fix file. Tested with a stand-in AI, so no real model is called in this task.
  - Files: create `src/fix_check/ai.py`, `tests/test_fix_check_ai.py`. Do not touch: `src/access_review/`, `planted/`, `heldout/`, `docs/EVALUATION.md`, `docs/fixcheck-plan.md`, `results/`. Never open `heldout/`. No Docker for the tests.
  - Steps:
    1. Read the "fix" part of a report (`src/access_review/report.py`, the golden files in `tests/golden/`). Write `fix_text(app_run)`, which returns only the fix sentences of a run's proved findings, with no table data beyond what the report itself shows a developer.
    2. Write `ask_ai(fix_text, ask)`: build the prompt from the saved prompt in `docs/fixcheck-plan.md`, call `ask` (a function; the real one is the AI chosen in the plan, the test one is a stand-in), and return the prompt, the raw answer and the SQL taken from it. The prompt contains the fix text and nothing else about the app.
    3. Write `python -m fix_check run ai --out DIR`: for each app and each attempt number in the plan it saves the prompt, the raw answer and the fix file under `fixes/ai/<app>/<n>/`, then runs `recheck`. An empty or unusable answer is recorded and fails condition 1. No retry.
    4. The answer is untrusted text: it is applied only inside the sandbox, never run on the host, and the AI is given no tools and no files.
    5. Tick M6.7 and update section 1.
  - Validation:
    - `pytest tests/test_fix_check_ai.py -v` passes. Assertions: the prompt built for an app contains its fix text and does not contain its table data, key entry, fixed twin or any word from the key; an answer that holds SQL gives one fix file; an answer with no SQL gives an empty fix that is recorded.
    - Negative control: the test feeds a stand-in AI that returns text meant to trick the tool (an instruction to ignore the checks); the run object is unchanged and the attempt is judged only by the four conditions.
    - `grep -rn heldout src/fix_check tests/test_fix_check_ai.py` prints nothing.
    - `python scripts/check_no_tuning.py` exits 0. `ruff check .` passes.
  - Done when: the AI path is tested with a stand-in and its prompt is shown to hold only the fix text.
  - Stop and ask if: the AI chosen in the plan needs a paid service or a new account; the fix text alone cannot name the table (that is a result, not a reason to feed the AI more).
- [ ] **M6.8 Run the fix check on the dev set.**
  - Depends on: M6.7.
  - Goal: raw outputs and score tables for the reference source and the AI source, every attempt recorded.
  - Files: create `results/fixcheck/reference/`, `results/fixcheck/ai/`, `results/fixcheck/RUN.txt`, `fixes/ai/**`, and the score tables. Bug fixes in `src/fix_check/` found in a dry run only. Do not touch: `src/access_review/`, `planted/`, `heldout/`, `docs/EVALUATION.md`, `docs/fixcheck-plan.md`. Never open `heldout/`. This task uses Docker.
  - Rule: the numbers of attempts come from `docs/fixcheck-plan.md` and are not changed. No fix, prompt, probe or rule is changed after seeing a result.
  - Steps:
    1. `docker ps -a` shows no sandbox container. `git status --short` prints nothing. Write `results/fixcheck/RUN.txt` with `git rev-parse HEAD`, the AI and its version, and the date.
    2. Run `python -m fix_check run reference --out results/fixcheck/reference`, alone. Save the table to `results/fixcheck/score-reference.txt`.
    3. Run `python -m fix_check run ai --out results/fixcheck/ai`, in the background and alone, and wait for it. Save the table to `results/fixcheck/score-ai.txt`.
    4. A crash before any result is saved may be repeated once. An attempt that produced a result is never repeated or replaced. Crashes and repeats are listed in the PR and in `ASSUMPTIONS.md`.
    5. A failed attempt stays in the totals with the conditions it broke. Do not edit a fix file by hand.
    6. Tick M6.8 and update section 1.
  - Validation:
    - The number of run files in each folder equals the plan's total for that source. Assertion: no attempt was dropped.
    - Each table prints attempts, successes and the failure count per condition. Assertion: every failed attempt is counted under at least one condition (an attempt can break more than one).
    - `git diff --name-only <hash in RUN.txt> -- src/access_review planted heldout docs/EVALUATION.md docs/fixcheck-plan.md` prints nothing.
    - `python scripts/check_no_tuning.py` exits 0. `ruff check .` passes. `python scripts/check.py` prints ALL PASS, run once and alone after the Docker runs finish. `docker ps -a` shows no leftover sandbox container.
  - Done when: both folders hold every attempt, `RUN.txt` records the commit, and the PR names every crash, repeat and not-checkable attempt.
  - Stop and ask if: the AI is not reachable or needs payment; a run would need a change to a frozen file.
- [ ] **M6.9 Fix-check results page.**
  - Depends on: M6.8.
  - Goal: one page that shows, per fix source, attempts, successes and which condition each failure broke, and a test that re-scores it from the saved runs.
  - Files: create `docs/fixcheck-results.md`, `tests/test_fixcheck_results.py`. Do not touch: `results/` raw files, `src/access_review/`, `docs/EVALUATION.md`, `planted/answer_key.json`.
  - Steps:
    1. Two tables, one per fix source, never added together. Columns: attempts, successes (counts first, ratio second), failures that broke condition 1, 2, 3 and 4 (an attempt can appear in more than one). Under each table list every failed attempt by app, number and broken conditions.
    2. A line that this is the dev set, a self-check, never quoted as accuracy, and a line that a success means the four conditions held for that attempt, which is not proof that the app is safe. Wording: "No violation found under this test." Never "secure".
    3. A short "How to check by hand" section: for any attempt, the paths of the fix file, the run object and the key entry, so G6 can be done.
    4. Tick M6.9 and update section 1.
  - Validation:
    - `pytest tests/test_fixcheck_results.py -v` passes. It re-reads every saved run object and asserts every number in the page equals the recount, and that the attempts equal the plan's totals.
    - Negative control: the test, run on a copy of the page with one number changed, fails.
    - `grep -n -i secure docs/fixcheck-results.md` prints nothing. `ruff check .` passes.
  - Done when: `docs/fixcheck-results.md` is merged and its test passes in CI.
  - Stop and ask if: a number cannot be reproduced from the saved runs; the two sources would need to be combined.
- [ ] **G6 (owner).**
  - Depends on: M6.9.
  - Maneet checks the fix check by hand for two attempts: one that passed and one that failed. For each, open the fix file, the run object and the key entry named in the "How to check by hand" section of `docs/fixcheck-results.md`, and the attempt's recheck output. Each condition shown matches the run object, and the failed attempt names the condition it broke. Maneet signs off or lists what to fix.

### M7 Real public apps (outline)

- [ ] M7.1 Decision D6 and licence check. Cover names only.
- [ ] M7.2 Run `review` over the apps. Record how many rebuild and the reasons for the rest.
- [ ] M7.3 Maneet labels each finding: clear bug, depends on intent, cannot tell. Never scored.
- [ ] M7.4 A test that scans committed files for owner names and repo URLs.

### M8 to M10 (goals and decision points only)

- **M8 Questions.** Ask the developer only where the code cannot settle intent. The language model only words questions, through one narrow interface that cannot change a finding status (a test enforces it). A planted comment in a migration must not change any finding (injection test). Starts only after the survey and interview data exist.
- **M9 Delivery.** The GitHub Action first (same command, JSON output, schema version checked), then a local web page where a person adds a project and re-runs the review. Only the user's own code. No hosted service.
- **M10 Handover.** Install in five minutes, error messages that say what to do next, a README demo, and an evidence pack for the report.

## 8. Later, not specified

A second platform (Firebase or Postgres with another login system), storage buckets, edge functions, reading the app's TypeScript (read only, to see which tables and functions it calls), a hosted version.

Follow-ups (found during a task, logged, not yet fixed; each needs its own task):

- Done: materialized views are now covered by the view test (V1), with planted app `views-02-matview-leak`. Found in M3.6 (PR 51).

### Planned extras (not tied to a gate)

These are ideas recorded as future work. None is started and none has a task ID, so none is eligible under rule 2 until a later PR turns it into a task. Nothing here changes an M6 task, a gate, or a frozen file: `docs/EVALUATION.md`, `docs/baselines.md`, `planted/`, `heldout/`, `src/access_review/`, the saved files under `results/` and the existing scripts. Every extra view is a new file, built from the saved runs, and is labelled "extra view, not the protocol score". How and when to schedule each item is AGENT-decides, logged in `ASSUMPTIONS.md`. The exceptions are a change to the protocol score and anything that touches a frozen file: Maneet decides those, in their own PR.

| ID | Item | What it is | Who decides |
| --- | --- | --- | --- |
| P1 | Extra views of existing results | Paired credit (a flaw counts only if the vulnerable run finds it and its fixed twin stays silent). A combined score in the Youden style (true-positive rate minus false-positive rate). Control tools that flag everything and flag nothing, scored by the same scorer. The unmapped count shown beside each baseline. Each is labelled "extra view, not the protocol score". | Scheduling: AGENT-decides, logged. Making any of these the protocol score, or editing `docs/EVALUATION.md`: DECISION by Maneet, own PR. |
| P2 | Execute the baselines' claims | Replay each mapped baseline claim through our probes in the sandbox, to see whether it is real. Today baseline findings are "reported, not executed" (PR 66). It cannot change our tool's numbers. Baseline precision could rise, and some matches might fail to reproduce. | Scheduling and an extra view: AGENT-decides, logged. Replacing the baseline numbers in `docs/results.md` or `docs/baselines.md`: DECISION by Maneet, own PR. |
| P3 | Second independent test round, after M8 | A new freeze tag and a new held-out set, written by someone who has not seen the tool's rules. Ideally a second labeller or an outside key, and AI-written apps from a different model than the one that helped build the tool. The plan is committed before the run. Same scorer. | Scheduling and the plan: AGENT-decides, logged. Reviewing the key and choosing the second labeller: Maneet, as at G4. Any rule change that comes before it: DECISION by Maneet. |
| P4 | Stability repeats of dev-set runs | Run the dev set several times and check that the findings do not change. The number of repeats is written before the first repeat. Output goes to a new folder under `results/`. Nothing existing is overwritten. | AGENT-decides, logged. |
| P5 | Read-only research notes (no code) | (a) Why the advisors' always-true SELECT lint is unmapped (`docs/baselines.md`, section 3.3). Do not change the unmapped rules or the mapping: that would be tuning. (b) What reusable test SQL the pgrls and rlsautotest repos hold. (c) The BAC-Bench data file: does it hold apps with SQL migrations and an outside key. Notes are a new docs file. Real-app names stay out (rule 10). | AGENT-decides, logged. |

Open questions, from the discussion log. Parked means no plan yet. Planned means an item above covers it.

| # | Question | Status | Owner |
| --- | --- | --- | --- |
| 1 | How should false alarms on tables that are public on purpose be handled? | Parked. M8 is the planned route. | Maneet |
| 2 | Which extra checks does Maneet want, and does the freeze allow paired credit or a combined score? | Planned: P1 as extra views. A protocol-score change needs a DECISION. | Maneet |
| 3 | Can real apps be found with an outside key? | Planned: P5(c). | Agent reads, Maneet decides use |
| 4 | Do pgrls and rlsautotest ship reusable test SQL? | Planned: P5(b). | Agent |
| 5 | Why is the advisors' always-true SELECT lint unmapped? | Planned: P5(a). | Agent |
| 6 | How is the M8 question step tested if intent cannot be known on real apps? | Parked until M8. | Maneet |
| 7 | Which second platform, and when? | Parked (section 8). | Maneet |
| 8 | Is there a second labeller or an outside list for the 13 flaw types? | Planned inside P3. | Maneet |
| 9 | Where does "execute the baselines' claims" go, and who decides? | Planned: P2, decided here. | Agent schedules, Maneet decides any score change |
| 10 | Which fixes for held-out misses are chosen for general reasons, and who writes the next held-out set? | Parked. Any rule fix needs a new freeze tag and a new held-out set (P3). | Maneet |

Known gaps, causes not yet read. Reading a cause is allowed and is a note only. Fixing exactly the held-out misses would be tuning and would inflate the next score. Any rule or probe change needs a DECISION by Maneet, a new freeze tag and a new held-out set.

- A big real app (300 to 400 migrations) has never been tried. If tried, it is a case study, not a score.
- Six held-out runs of our tool ended in a probe error. The causes are unread.
- The cause of the `swap_offers` R7 miss on the held-out set is unknown.
- One pgrls rule behind the R1 false alarm on `pantry-share/fixed` is untraced.
- `decoy-02-public-profile-read` gave `needs_decision` in 5 of 5 re-runs. The earlier "no finding" run never reproduced and its cause is unknown.

## Appendix A: Flaw catalogue (the key is written from this)

| Id | Group | Plain description | OWASP |
| --- | --- | --- | --- |
| R1 | Rows | A visitor can read rows they should not | A01, API1 |
| R2 | Rows | A signed-in user can read other users' rows | A01, API1 |
| R3 | Rows | A visitor can insert rows | A01 |
| R4 | Rows | A user inserts a row with someone else's owner id | A01, API1 |
| R5 | Rows | A user changes another user's row | A01, API1 |
| R6 | Rows | A user deletes another user's row | A01, API1 |
| R7 | Rows | A user changes a row's owner and takes it over | A01, API1 |
| C1 | Columns | A user writes a protected column (role, admin, paid) | API3 |
| C2 | Columns | A private column is readable by those who should not see it | API3 |
| V1 | Views | A view shows rows the table underneath would hide | A01 |
| U1 | Functions | A function with elevated rights runs without checking the caller | API5 |
| U2 | Functions | An admin-only function can be called by any user | API5 |
| U3 | Functions | A function can be called by a visitor by default | API5 |

## Appendix B: Answer key shape

```json
{
  "rows-01-profiles": {
    "flaws_vulnerable": [
      {"flaw_id": "R1", "table": "profiles", "actor": "visitor", "action": "read"}
    ],
    "flaws_fixed": [],
    "allowed": [
      {"actor": "user-a", "action": "read", "table": "profiles", "expect": "own_row_only"}
    ],
    "decoy": false
  }
}
```

## Appendix C: Checks

```
ruff check .
pytest -v
bandit -r src -ll
pip-audit --skip-editable
```

## Appendix D: Rules that protect the evaluation

1. The answer key comes from Appendix A and is reviewed by Maneet. It is never edited to match probe output.
2. Dev apps and held-out apps are different sets, written by different sessions.
3. The held-out set is run once. After it, no tuning.
4. The score for an app is never quoted without its raw outputs saved.
5. Real public apps are never scored.
