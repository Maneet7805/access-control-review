# Fix-check results

This is the dev set. It is a self-check, never quoted as accuracy. The tool and the 15 apps were built together.

A success here means the four conditions held for that attempt. That is not proof that the app is safe. The wording for a clean result is "No violation found under this test."

The four conditions (`docs/EVALUATION.md` section 6):

1. The app still builds with the fix.
2. The same attack now fails (the tool's own review of the fixed copy finds none of the app's planted flaws).
3. What was allowed still works (every entry in the app's `allowed` list that is not an expected failure).
4. No new problem (the tool's own review finds no proved finding the vulnerable app did not already have).

If condition 1 fails, conditions 2 to 4 are not run. An attempt can break more than one condition, so the "Broke" columns can add to more than the number of failures. The two sources are never added together.

## Reference fixes

| Source | Attempts | Successes | Broke 1 | Broke 2 | Broke 3 | Broke 4 |
| --- | --- | --- | --- | --- | --- | --- |
| Reference | 15 | 15 of 15 (100%) | 0 | 0 | 0 | 0 |

Failed attempts:

- None.

## AI fixes

| Source | Attempts | Successes | Broke 1 | Broke 2 | Broke 3 | Broke 4 |
| --- | --- | --- | --- | --- | --- | --- |
| AI | 45 | 33 of 45 (73%) | 0 | 6 | 9 | 3 |

Failed attempts (app, attempt number, conditions broken):

- rows-02-profiles-all-authenticated, attempt 1: broke 2+3
- rows-02-profiles-all-authenticated, attempt 2: broke 2+3
- rows-02-profiles-all-authenticated, attempt 3: broke 2+3
- writes-01-visitor-insert, attempt 1: broke 2
- writes-01-visitor-insert, attempt 2: broke 2
- writes-01-visitor-insert, attempt 3: broke 2
- functions-02-security-definer-no-check, attempt 1: broke 3
- functions-02-security-definer-no-check, attempt 2: broke 3
- functions-02-security-definer-no-check, attempt 3: broke 3
- functions-03-default-execute, attempt 1: broke 3+4
- functions-03-default-execute, attempt 2: broke 3+4
- functions-03-default-execute, attempt 3: broke 3+4

## What the saved files show about the failures

Only what the run objects and fix files record. Where they do not say, this page says "cannot tell".

- `rows-02-profiles-all-authenticated`: the fix adds a new owner-only read policy. It drops only that new name. The old policy "any signed-in user" is not dropped, so the old permissive rule stays. The run object says the flaw is "still proved". Why the own-row read check (condition 3) also failed: cannot tell.
- `writes-01-visitor-insert`: the fix adds a new insert policy for signed-in users. It drops only that new name. The old policy "anyone adds" is not dropped. The run object says the flaw is "still proved".
- `functions-02-security-definer-no-check`: the fix changes the function to run with the caller's rights and limits who can call it. The run object says the own-row update through the function did not hold (condition 3). The run object does not say why.
- `functions-03-default-execute`: the fix revokes the default call right from visitors and gives it to signed-in users. It does not change the function's rights. The run object says a new finding "U1 on note_count" appeared (condition 4) and the own-rows count did not hold (condition 3). Why: cannot tell.
- All three attempts of each of these four apps broke the same conditions. For these apps the three attempts are the same fix in different words as far as the run objects show. Whether they are textually identical: not checked.

## What this result does not say

- The AI source is 45 attempts: 3 per app on 15 apps, one assistant. The model is recorded in `results/fixcheck/RUN.txt`: claude-opus-5-5 (Claude Code command line, version 2.1.327).
- The AI and the tool's author are the same assistant family. The plan lists this as a weakness (`docs/fixcheck-plan.md` section 8).
- The first launch of the 45 AI attempts never reached the AI (a wrong command path). Those 45 saved results are not model results. They are excluded from every number here and kept in `results/fixcheck/launch-fault/`. The AI numbers above come from the rerun.
- The plan's limits (`docs/fixcheck-plan.md` section 8):
  - It runs on the 15 prototyped apps built together with the tool. It says nothing about other apps.
  - Condition 3 only checks the entries in the key's `allowed` lists. Behaviour that no entry lists is not checked.
  - Conditions 2 and 4 use the tool's own review. A flaw the tool cannot detect cannot be seen as fixed or as newly introduced.
  - An AI answer is not the same twice. Three attempts per app show a spread, not a stable rate.
- These numbers do not say the AI is bad, and they do not say the tool is right.

## How to check by hand

For any attempt, three things are needed:

- The fix file. AI: `fixes/ai/<app>/<n>/fix.sql` (the prompt and the raw answer sit beside it as `prompt.txt` and `answer.txt`). Reference: `fixes/reference/<app>.sql`.
- The run object, with the four conditions and their detail lines. AI: `results/fixcheck/ai/<app>__<n>.json`. Reference: `results/fixcheck/reference/<app>__1.json`.
- The key entry: the object named `<app>` in `planted/answer_key.json`. It lists the planted flaws and the `allowed` entries.

Good examples for gate G6:

- Passed: `writes-02-spoofed-owner`, AI attempt 1. Fix `fixes/ai/writes-02-spoofed-owner/1/fix.sql`, run object `results/fixcheck/ai/writes-02-spoofed-owner__1.json` (all four conditions `pass`), key entry `writes-02-spoofed-owner`.
- Failed: `rows-02-profiles-all-authenticated`, AI attempt 1. Fix `fixes/ai/rows-02-profiles-all-authenticated/1/fix.sql`, run object `results/fixcheck/ai/rows-02-profiles-all-authenticated__1.json` (`broken` is `[2, 3]`), key entry `rows-02-profiles-all-authenticated` (flaw R2 on `profiles`). The old policy is in `planted/rows-02-profiles-all-authenticated/vulnerable/migrations/`.

The per-attempt lines are also in `results/fixcheck/score-reference.txt` and `results/fixcheck/score-ai.txt`. The test `tests/test_fixcheck_results.py` recounts this page from the run objects.
