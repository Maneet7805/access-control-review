# Fix check plan

This plan is written and merged before any fix is run (`docs/ROADMAP.md`, M6.1). After the first fix run (M6.8) it does not change. It does not change `docs/EVALUATION.md`: what counts as a successful fix is fixed in section 6 of that file, and this plan only says how it is applied.

## 1. What is tested

After the tool reports a flaw, it gives the developer a fix text. The fix check asks: if that fix is applied, is the flaw gone, and does the app still work for the people who are allowed in?

A fix is a new migration file added to a copy of the vulnerable app. The tool never edits the developer's files, and the copy is made outside `planted/`.

The fix check runs on the dev set only. It is a self-check, because the tool and the dev set were built together. It is never quoted as accuracy.

## 2. The apps in the fix check

An app is in the fix check when the key has at least one planted flaw for its `vulnerable/` side, and the app has both a `vulnerable/` and a `fixed/` folder. These apps are out, because there is nothing to fix:

- the decoys (`decoy-01`, `decoy-02`, `decoy-03`) and the clean apps (`clean-01`, `clean-02`), which have no planted flaw and no twin;
- `rows-03-locked-out`, which has only a `fixed/` folder;
- `hostile-01-callout`, which has no key entry.

The count is taken from the key by this one-line script, run from the repository root. The script reads the key and checks that the two folders exist; it does not read inside them.

```
python -c "import json,pathlib as p;k=json.load(open('planted/answer_key.json'));a=[n for n,v in k.items() if v['flaws_vulnerable'] and (p.Path('planted')/n/'vulnerable').is_dir() and (p.Path('planted')/n/'fixed').is_dir()];print(len(a),len(a)*3);print(*a,sep='\n')"
```

Its output, on the key at the freeze tag `eval-freeze-1`:

```
15 45
rows-01-profiles
rows-02-profiles-all-authenticated
writes-01-visitor-insert
writes-02-spoofed-owner
writes-03-update-others
writes-04-delete-others
functions-01-admin-delete-any-user
functions-02-security-definer-no-check
functions-03-default-execute
writes-05-owner-change
columns-01-self-admin
columns-02-self-paid
views-01-bypass
views-02-matview-leak
columns-03-phone-exposed
```

The first number is the count of apps (15). The second is that count times 3 (45), the AI total in section 3. A later task that finds a different number from the script stops and asks.

## 3. Fix sources and number of attempts

One attempt is one app and one fix. There are two fix sources. Their numbers are reported separately and never added together.

| Source | Attempts per app | Apps | Total attempts |
| --- | --- | --- | --- |
| Reference | 1 | 15 | 15 |
| AI | 3 | 15 | 45 |

Reference source. The fix is the difference between the app's `vulnerable/` and `fixed/` migration files, written once as one SQL file (`fixes/reference/<app>.sql`). It is the twin's change, not a fix written to pass the checks. If a reference fix does not pass, it stays as it is and is reported.

AI source. Three independent attempts per app. No retry after a failure, no feedback from one attempt to the next, and no attempt is dropped or repeated to get a better number. Every attempt is recorded, including empty answers and attempts that fail.

A crash before any result is saved may be repeated once (M6.8). An attempt that produced a result is never repeated or replaced.

## 4. The AI and its prompt

The AI is a fresh session of the coding assistant already used on this project. It is given no tools and no files. Each attempt is its own fresh session, so one attempt cannot see another. The model name and version are written to `results/fixcheck/RUN.txt` before the first AI attempt (M6.8), taken from the session itself.

What the AI sees: only the fix text from the tool's report for the vulnerable app. This is what a developer would paste into their own AI assistant. The fix text is the "Suggested fix" sentence of every proved finding of the vulnerable run, in report order, one paragraph each. The AI never sees the code, the migrations, the key, the fixed twin, the findings' table data, any score or any earlier attempt. If the fix text alone cannot name the table, that is a result. The AI is not given more.

Weakness, stated up front: the AI is the same assistant family as the one that helped build the tool. It may phrase fix text and SQL in ways that suit the tool's own fix wording. The AI source therefore tests this one assistant on this tool's text. It does not show how other assistants behave.

The prompt is fixed text. It is saved here and is not changed after the first run. `{FIX_TEXT}` is the only part that changes between apps.

```
A developer prototyped an app on Supabase (PostgreSQL). A test tool found access-control problems in the app's database and wrote the fix text below.

Write one SQL migration that applies these fixes.

Rules:
- Reply with one SQL code block and nothing that needs to be run outside it.
- You cannot see the app's code. Name only the tables, columns and functions that the fix text names.
- Do not drop tables and do not delete data.
- Keep the app working for the people who are meant to use it.

Fix text:

{FIX_TEXT}
```

How an answer becomes one SQL file:

1. The raw answer is saved as it came, with the prompt.
2. The SQL is the text inside the fenced code blocks of the answer (a block tagged `sql`, or an untagged block), joined in order with a blank line between them. Text outside the blocks is ignored.
3. That text is saved as one file and added to a copy of the vulnerable app as the last migration (M6.4).
4. An answer with no fenced block, an empty block, or text that is not SQL text is saved as an empty fix. An empty or unusable answer is an attempt that fails condition 1. It stays in the totals.
5. The answer is untrusted text. It is applied only inside the sandbox, never run on the host. Anything in it that tries to steer the tool has no effect: the attempt is judged only by the four conditions.

## 5. The four conditions

From `docs/EVALUATION.md` section 6. An attempt succeeds only when all four hold.

1. The app still builds. The old migrations plus the fix apply without an error, and the rebuilt app can be tested.
2. The same attack now fails. The tool's review of the fixed copy finds none of the planted flaws of that app.
3. What was allowed still works. Every entry in the app's `allowed` list, that is not marked `expected_failure`, still holds (for example, a user can still read their own row). An app with an empty `allowed` list passes this condition because there is nothing to check, and the output says so.
4. No new problem. The review of the fixed copy shows no proved finding that the vulnerable app did not already have (same flaw id and same target).

A fix that locks everyone out fails condition 3. A fix on the wrong table fails condition 2.

How a failed attempt is labelled. A failed attempt is labelled with the list of conditions it broke, for example `3` or `2+4`. An attempt can break more than one. If condition 1 fails, conditions 2 to 4 are "not run": the label is `1` only, and they are never counted as passed. An attempt that passes all four is labelled `ok`. Every failed attempt is counted under at least one condition.

## 6. The table M6.9 will print

Two tables on `docs/fixcheck-results.md`, one for each fix source, never added together.

| Source | Attempts | Successes | Broke 1 | Broke 2 | Broke 3 | Broke 4 |
| --- | --- | --- | --- | --- | --- | --- |
| Reference | count | x of n (ratio) | count | count | count | count |
| AI | count | x of n (ratio) | count | count | count | count |

- Counts come first and the ratio second, for example "11 of 15".
- An attempt that broke two conditions appears in two "Broke" columns, so the four columns can add to more than the number of failures.
- Under each table, every failed attempt is listed by app, attempt number and the conditions it broke.
- The page says that this is the dev set and a self-check, never accuracy. It says that a success means the four conditions held for that attempt, and that this is not proof the app is safe to run in production. The wording for a clean result is "No violation found under this test."
- The page lists, for any attempt, the paths of the fix file, the run object and the key entry, so a person can check it by hand.

## 7. Out of scope

- The held-out set (`heldout/`) is not used: not read, not listed, not run, not used for fixes.
- No tuning of fixes, prompts or tools after a result is seen. A bug fix to the fix-check code is allowed only for something found in a dry run, before the first recorded run.
- Real public apps are not fixed and not scored.
- No change to `planted/answer_key.json`, to `src/access_review/` or to `docs/EVALUATION.md`.
- No paid service and no new account. If the AI cannot be reached without one, the task stops and asks.

## 8. Limits of this test

- It runs on 15 prototyped apps built together with the tool. It says how the tool's fix text and one assistant behave on these apps. It does not say how they behave on other apps.
- The AI and the tool's author are the same assistant family (section 4).
- Condition 3 only checks the entries in the key's `allowed` lists. A behaviour that no entry lists is not checked.
- Condition 2 and condition 4 use the tool's own review. A flaw the tool cannot detect cannot be seen as fixed or as newly introduced.
- The answer from an AI is not the same twice. Three attempts per app show the spread. They do not give a stable rate.
