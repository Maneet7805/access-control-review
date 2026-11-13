# Roadmap: access-control-review

Put this file at `docs/ROADMAP.md`. Claude Code reads it, picks the next eligible task, builds it, proves it works, ticks the box and reports. Maneet supervises and merges.

How much detail each part has:
- M0 to M4 are written in full. They are the current work and the next work.
- M5 to M7 are medium detail. They are rewritten in full when their turn comes.
- M8 to M10 are goals and decision points only. Details written months early go stale, and they depend on what M1 and M2 teach us.

## 1. Where we are (the agent updates this after every PR)

| Milestone | Plain-English purpose | Progress |
| --- | --- | --- |
| M0 Harness | Repo, CI, rules, roadmap | 7/7 |
| M1 Honest foundations | A sandbox that behaves like real Supabase, is safe, and checks allowed access too | 8/9 |
| M2 Thin slice | One app, one attack, one plain-language report, end to end | 0/6 |
| M3 More attacks | Write rows, protected columns, views, functions, plus decoy apps | 0/9 |
| M4 Evaluation frozen | Scoring rules, held-out test apps and a freeze tag, before any scoring | 0/5 |
| M5 Compare | Run other tools on the same apps and score everyone | 0/6 |
| M6 Fix check | Does the suggested fix remove the flaw without breaking the app | 0/3 |
| M7 Real apps | Unscored case studies on public apps | 0/4 |
| M8 Questions | Ask the developer when the code cannot decide | later |
| M9 Delivery | GitHub Action, then a local web page | later |
| M10 Handover | Docs, install experience, evidence pack for the report | later |

- Current milestone: M1
- Last merged PR: #30
- Next eligible task: M2.1 Evidence model
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

- [ ] **M2.1 Evidence model.**
  - Depends on: G1.
  - Goal: a probe returns what it ran and what it saw, not raw rows.
  - Files: `src/access_review/evidence.py`, `src/access_review/probes.py`, `tests/test_evidence.py`.
  - Shape: `{probe, actor, statement, result, rows_seen, error}`. Serialises to JSON.
  - Validation: round-trip to JSON and back is equal. The two existing probes return evidence. Existing planted tests still pass.
- [ ] **M2.2 Finding model and JSON schema, version 0.1.**
  - Depends on: M2.1.
  - Goal: one fixed shape for a finding that later parts can rely on.
  - Files: `src/access_review/findings.py`, `schemas/finding.schema.json`, `tests/test_findings.py`.
  - Fields: `schema_version`, `id`, `flaw_id` (Appendix A), `owasp`, `table` or `column` or `function`, `actor`, `proof` (evidence), `explanation`, `fix`, `status`. Status is only `proved` or `needs_decision`. Nothing is `proved` without evidence.
  - Validation: sample findings validate against the schema. A finding with no evidence is rejected (negative control).
- [ ] **M2.3 First rule: another user's rows are readable.**
  - Depends on: M2.2.
  - Goal: turn evidence from `user_reads_rows` into a finding.
  - Files: `src/access_review/rules.py`, `tests/test_rules.py`.
  - Logic: if the table has an owner column that references `auth.users` and the actor sees rows owned by someone else, the finding is `proved`. If the table has no owner column and a visitor can read it, the status is `needs_decision` (it may be public on purpose). Never guess intent.
  - Validation: `rows-01` and `rows-02` vulnerable give one proved finding each. Both fixed twins give none. A new decoy `decoy-01-public-posts` (a table meant to be public, no owner column) gives `needs_decision` and not `proved`. Update the key for it (needs approval).
- [ ] **M2.4 Plain-language report.**
  - Depends on: M2.3.
  - Goal: `report.md` that a novice can read.
  - Files: `src/access_review/report.py`, `tests/test_report.py`, `tests/golden/`.
  - Content per finding: what is wrong in one sentence, who can do it, the proof (the exact statement and what came back), and a fix as text the developer can give to their own AI. When no finding: the exact sentence "No violation found under this test." The tool never changes the developer's code.
  - Validation: golden-file test for each planted app. A jargon test: terms such as "RLS", "policy", "anon", "JWT" must be explained in plain words the first time they appear in a report. A test asserts the word "secure" never appears except inside "No violation found under this test."
- [ ] **M2.5 Command line.**
  - Depends on: M2.4.
  - Goal: `python -m access_review review <migrations_dir> --out report.md`.
  - Files: `src/access_review/cli.py`, `tests/test_cli.py`.
  - Validation: on `rows-01` vulnerable, exit code 1 and a report with one finding. On the fixed twin, exit code 0 and the "No violation" sentence. On a broken migration, exit code 2 and the reason (M1.7).
- [ ] **G2 (owner).** Maneet runs the command on the vulnerable and the fixed twin, and reads both reports. Is the vulnerable report understandable to a classmate who has never heard of row security? Maneet signs off or lists what to reword.

### M3 More attacks

All M3 tasks depend on G2. M3.1 to M3.8 can be done in any order. M3.9 depends on all of them.

Pattern for every task below: add the probe, add a planted vulnerable and fixed pair using the flaw ids in Appendix A, add the key entries, and add a negative control. Each new probe returns Evidence (M2.1) and each new rule returns a Finding (M2.2).

- [ ] **M3.1 Insert as a visitor and as a user with someone else's owner id (R3, R4).** Apps: `writes-01-visitor-insert`, `writes-02-spoofed-owner`. Validation: the vulnerable apps accept the insert, the fixed ones refuse it. All writes run inside a transaction that is rolled back.
- [ ] **M3.2 Update and delete another user's row (R5, R6).** Apps: `writes-03-update-others`, `writes-04-delete-others`. Same validation.
- [ ] **M3.3 Take over a row by changing its owner (R7).** App: `writes-05-owner-change`, missing check on new values. Validation: after the update the row belongs to the attacker (assert).
- [ ] **M3.4 Protected column is writable by the user (C1).** Apps: `columns-01-self-admin` (a user sets their own `role` or `is_admin`), `columns-02-self-paid`. The probe updates a protected column on the actor's own row. Which columns count as protected comes from names like `role`, `is_admin`, `balance`, `paid`, `owner_id`, and from the key. If unsure, status `needs_decision`.
- [ ] **M3.5 Private column is readable by others (C2).** App: `columns-03-phone-exposed`, a public profile table that also exposes phone numbers. Probe: read a private-looking column as another user or visitor.
- [ ] **M3.6 A view that bypasses row security (V1).** App: `views-01-bypass`. A view created without the caller's rights shows everyone's rows even though the table underneath is locked. Validation: vulnerable view leaks, fixed view does not. Read the Supabase page on views in full and cite it in the PR.
- [ ] **M3.7 Functions: a signed-in user or visitor can call something they should not (U1, U2, U3).** Apps: `functions-01-admin-delete-any-user`, `functions-02-security-definer-no-check`, `functions-03-default-execute`. Probe: call each function with typed dummy arguments inside a savepoint that is rolled back, and record success, permission denied or other error. Status is `proved` only when the call actually ran.
- [ ] **M3.8 Decoys and clean apps.** Apps: `decoy-02-public-profile-read` (public on purpose), `decoy-03-shared-team-table`, `clean-01-all-correct`, `clean-02-all-correct-different-style`. Validation: zero `proved` findings on clean apps. Decoys give `needs_decision`, never `proved`. This is the false-alarm test.
- [ ] **M3.9 The tests must have teeth.**
  - Depends on: M3.1 to M3.8.
  - Goal: prove the tests can fail.
  - Files: `tests/test_teeth.py`.
  - Steps: for each probe, a test swaps it for a broken version (always returns nothing, or always returns everything) and asserts the planted-app tests fail.
  - Validation: `pytest tests/test_teeth.py` passes, meaning every broken probe is caught.
- [ ] **G3 (owner).** Maneet runs the command on any three planted apps from different groups and reads the reports. Then Maneet reads `planted/answer_key.json` for one app and checks it agrees with Appendix A.

### M4 Evaluation protocol frozen

Why before scoring: if the answer key or the rules change after seeing results, the results mean nothing.

- [ ] **M4.1 Write `docs/EVALUATION.md`.**
  - Depends on: G3.
  - Contents: definitions of recall (planted flaws found / planted flaws), precision (findings that match a planted flaw / all proved findings), false alarm (proved findings on fixed twins, clean apps and decoys). The matching rule (same app, same flaw id, same table or column or function). How `needs_decision` is counted (reported separately, never as a finding). What counts as a successful fix (M6). No target numbers are promised.
  - Needs Maneet's approval.
- [ ] **M4.2 Scoring module.**
  - Depends on: M4.1.
  - Files: `src/access_review/scoring.py`, `tests/test_scoring.py`. It reads findings JSON and the answer key only. It must not import probes, rules or the sandbox (a test checks the imports).
  - Validation: hand-written findings give hand-computed recall, precision and false alarms. Negative control: dropping one finding lowers recall by the expected amount.
- [ ] **M4.3 Dev-set run.**
  - Depends on: M4.2.
  - Goal: `python -m access_review.scoring planted/` prints a score table for our own tool on the dev set. Expected on the dev set: every planted flaw found and zero false alarms, since we built the dev set alongside the tool. This is a self-check, not a result. It is never quoted as accuracy.
- [ ] **M4.4 DECISION D3 and the held-out set.**
  - Goal: apps the tool's author never saw.
  - Process: a fresh session is given only Appendix A and the answer key shape, and writes pairs in a different style (other table names, other policy styles, other schema layouts), including decoys and clean apps. The files go in `heldout/`, which is not read by the coding agent until M5.4.
  - Validation: the held-out files validate against the key shape. Maneet reviews the key.
- [ ] **M4.5 Freeze.**
  - Goal: tag the repo `eval-freeze-1` once G4 is signed. After the tag: no changes to probes, rules or the key without a DECISION, and any such change means the held-out set must be rewritten and rerun.
- [ ] **G4 (owner).** Maneet reads `docs/EVALUATION.md`, confirms it, and creates the tag.

### M5 Compare with other tools (outline, rewritten in full at G4)

- [ ] M5.1 Decision D4: choose baselines. Candidates: Semgrep, Supabase advisors, rlsautotest, pgrls, rlsgrid, SupaShield. Check each tool's licence and how it runs without a network.
- [ ] M5.2 Record the exact commands to run each baseline on a rebuilt planted app in `docs/baselines.md`, after reading each tool's page in full.
- [ ] M5.3 An adapter per baseline that turns its output into the same shape the scorer reads. Each adapter has a test with a sample output.
- [ ] M5.4 Run all tools on the dev set. Then, once, on the held-out set. Save the raw outputs and the score table.
- [ ] M5.5 Rule: nothing is tuned after the held-out run. If it must be, the held-out set is replaced.
- [ ] M5.6 Write the results table for the report.
- [ ] **G5 (owner).** Maneet checks the table against the raw outputs for two apps by hand.

### M6 Fix check (outline)

- [ ] M6.1 A fix is a new migration file added to a copy of the vulnerable app.
- [ ] M6.2 `recheck` command: reports (a) migrations apply, (b) the same attack now fails, (c) the allowed list still passes, (d) no new leak. Negative controls: a fix that locks everyone out fails (c). A fix on the wrong table fails (b).
- [ ] M6.3 Run it on the dev set with fixes from the reference twin and from an AI that only sees the report's fix text (D5). Record each run.
- [ ] **G6 (owner).**

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
