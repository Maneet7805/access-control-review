# Evaluation protocol

This file fixes how the tool is scored, before any score exists. The answer key (`planted/answer_key.json`) is written from the flaw catalogue (`docs/ROADMAP.md`, Appendix A), never from what a probe finds. After the freeze tag `eval-freeze-1` is created, this file, the key, the probes and the rules change only through a DECISION, and any such change means the held-out set is rewritten and run again.

No target numbers are promised. Scores are reported as counts first (for example "11 of 13") and as a ratio second.

## 1. What is scored

A run is one review of one folder of migrations. An app in the key has one to two folders:

- `vulnerable/`: the side with planted flaws. Expected set: the key's `flaws_vulnerable`.
- `fixed/`: the fixed twin. Expected set: the key's `flaws_fixed`, which is empty for every app.
- `migrations/`: an app with no twin (decoys and clean apps). Expected set: the key's `flaws_vulnerable`, which is empty for every such app.
- An app with only a `fixed/` folder (`rows-03-locked-out`) has one run, on the fixed side.

Only apps that have an entry in the key are scored. `hostile-01-callout` has no key entry and is not scored.

A run is of one of two kinds:

- Flawed run: the expected set is not empty. Every `vulnerable/` run of a flawed app.
- Clean run: the expected set is empty. Every `fixed/` run, every decoy, every clean app.

The dev set and the held-out set are scored separately. Their numbers are never merged or averaged.

## 2. Terms

- **Proved finding**: a finding with status `proved`. This is the only kind of finding that is scored.
- **needs_decision finding**: a finding with status `needs_decision`. It is not a finding for scoring (section 5).
- **Planted flaw**: one entry in the expected set of a flawed run. Two entries with the same flaw id on different tables are two planted flaws.
- **Duplicate**: two proved findings in the same run with the same flaw id and the same table, column and function. They differ only in actor or text. They count once. Findings with the same flaw id on different targets are different findings.

## 3. Matching rule

A proved finding matches a planted flaw when all of these hold:

1. Same app and same side. A finding from a `fixed/` run never matches an entry of the `vulnerable/` run.
2. Same flaw id.
3. Same target. The key entry names a `table`, a `column`, a `function`, or a table and a column together. Each of those fields that the entry names must equal the finding's field of the same name. Fields the entry does not name are ignored. A view is named in `table`.

The actor and the action in the key entry are not compared. The flaw id already says who does what, and a finding that names a different actor for the same flaw on the same target proves the same flaw.

A planted flaw is found when at least one proved finding matches it. A planted flaw is counted once however many findings match it. A finding that matches no planted flaw is unmatched.

## 4. Metrics

All counts are taken over every scored run of one set, after duplicates are removed.

- **Recall** = planted flaws found / planted flaws.
- **Precision** = proved findings that match a planted flaw / all proved findings. Proved findings on clean runs are in the denominator and can never be in the numerator.
- **False alarm**: a proved finding on a clean run (a fixed twin, a clean app or a decoy). Reported as two numbers: the count of false alarms, and the false-alarm rate = clean runs with at least one false alarm / clean runs.
- **Extra finding**: an unmatched proved finding on a flawed run. It lowers precision. It is not a false alarm, because it may be a real flaw the key does not list. Extra findings are listed by name next to the score so a reader can judge them. The key is not edited to absorb them.

A ratio with a zero denominator (no planted flaws, no proved findings, no clean runs) is printed as "n/a", never as 0 or 1.

Also printed beside every score, as plain counts:

- Not checkable: runs that could not be rebuilt (exit code 2 of the command line). A not-checkable flawed run finds nothing, so its planted flaws are misses. A not-checkable clean run gives no false alarm. Neither run is dropped from the totals.
- Probe errors: runs where a probe ended in an error and the report says so. A probe error is a miss, not a finding.
- needs_decision count (section 5).

Nothing in the score is waived because the tool has a known limit (section 8). A planted flaw outside the tool's limits is a miss.

The `allowed` lists in the key (what must keep working) are not part of recall, precision or false alarm. They are used in the fix check (section 6).

## 5. How needs_decision is counted

- A `needs_decision` finding is never in a numerator or a denominator of recall, precision or false alarm. It is never a finding and never a false alarm.
- It is reported separately: the count per run and the total per set, with the flaw id and target of each.
- The key never lists a `needs_decision` finding. A `needs_decision` finding that the key does not list is the normal case, not an error. It is counted in the tally and carries no penalty.
- A planted flaw that the tool reports only as `needs_decision` is not found. It is a miss, and the `needs_decision` is also in the tally.
- Known case, `columns-03-phone-exposed`: the vulnerable run gives the planted C2 (proved) and also an R1 `needs_decision` on the `directory` table. The key lists only C2. Result: C2 is found, the R1 `needs_decision` goes in the tally, nothing else changes.
- Known case, the decoys: `decoy-01-public-posts` gives an R1 `needs_decision`. `decoy-03-shared-team-table` gives no finding. Both score zero false alarms.
- Open question, `decoy-02-public-profile-read`: an earlier run reported no finding and a later run reported an R1 `needs_decision`. The cause was not found. Under this protocol both outcomes give zero false alarms, so the score does not depend on the answer. Only the `needs_decision` tally does. M4.3 re-runs the app and records which outcome it gives and how often.

The honest limit of this rule: a tool could avoid false alarms by only ever asking. That is why the `needs_decision` count is printed beside every score and is never left out of a table or a quote.

Worked example, for hand-computed tests (invented apps):

- App A, `vulnerable/`, key lists R2 on `p` and R5 on `p`. Proved: R2 on `p`, R6 on `p`. A `needs_decision` R1 on `q`.
- App A, `fixed/`: no findings.
- App B, a decoy: no proved finding. One `needs_decision`.
- App C, a clean app: proved R1 on `n`.
- Recall = 1/2 (R2 found, R5 missed). Precision = 1/3 (three proved findings, one matches). Extra findings: 1 (R6). False alarms: 1 (C). Clean runs: 3 (A fixed, B, C), so the false-alarm rate is 1/3. `needs_decision` tally: 2.
- Drop the R2 finding and recall falls to 0/2 and precision to 0/2.

## 6. What counts as a successful fix (used in M6)

A fix is a new migration file added to a copy of the vulnerable app. The tool never edits the developer's files. One attempt is one app and one fix. An attempt succeeds only when all four hold:

1. The migrations apply. The rebuilt app is checkable.
2. The same attack now fails. The review of the fixed copy gives no proved finding that matches any planted flaw of that app (section 3).
3. The allowed list still passes. Every `allowed` entry of the app that has no `expected_failure` still holds. An app with an empty `allowed` list passes this vacuously.
4. No new leak. The review of the fixed copy gives no proved finding whose flaw id and target are absent from the vulnerable app's proved findings.

Reported per fix source (the reference fixed twin, an AI that sees only the report's fix text): attempts, successes, and which of the four conditions each failure broke. A fix that locks everyone out fails condition 3. A fix on the wrong table fails condition 2. Every attempt is recorded, including failures. The number of attempts is set before the runs start.

## 7. How a score is produced and quoted

- The scorer reads findings JSON and the answer key only. It does not run probes, rules or the sandbox.
- Each run is labelled with its app and side. The label comes from the folder, not from the finding.
- A score is never quoted without its raw outputs saved. Real public apps are never scored.
- The dev set score is a self-check, because the tool and the dev set were built together. It is never quoted as accuracy.
- The held-out set is run once. After it, nothing is tuned. If something must change, the held-out set is replaced.
- Baseline tools (M5) are scored with these same rules, through adapters that map their output into the same findings shape.
- A result is worded "No violation found under this test." when no proved finding exists. It is never worded as proof that an app is safe.

## 8. What a score does not cover

The tool tests what its probes can execute. These limits come from the probe design and are recorded in `ASSUMPTIONS.md`. A held-out flaw that needs one of them is a miss and stays in the totals.

- Views: only a view over exactly one table in schema `public` is compared with its table. A materialized view over several tables, and any view in another schema, is not tested.
- Writes: only the first two users found in the app's seed data act. A table with a required column that the tool cannot fill, or an extra foreign key, is not tested for insert. Visitors are not tested for update or delete.
- Columns: a protected column (C1) and a private column (C2) are found by name lists, so a column with an unlisted name is not tested.
- Functions: only functions in schema `public` are called, with one harmless value per argument type. An argument type the tool cannot fill gives an error, not a finding.
- Intent: the tool cannot see what the developer meant. A table that shows private-named columns on purpose can still give a proved C2.
- Users: an app that seeds fewer than two users gets only the visitor tests.
