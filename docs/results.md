# Results

This page compares our tool with four existing tools on two sets of apps with planted flaws. Every number is a count first and a ratio second. Every number can be re-made from the saved raw outputs named under each table, and `tests/test_results_table.py` re-scores them and fails if this page disagrees. The scoring rules are in `docs/EVALUATION.md`; how each baseline is run and mapped is in `docs/baselines.md`.

- Held-out set first, dev set second. The two are never merged: no total, no average, no pooled row.
- The needs_decision count is in every row. A needs_decision finding is never counted as a finding, a hit or a false alarm.
- Our tool is run (`executed`). The baselines are `reported, not executed`: we read what they report and map it to our findings shape (`docs/baselines.md` section 3).
- A result with no proved finding means "No violation found under this test." It is not a statement about the app.

## Held-out set

Written by a separate session that saw only the flaw catalogue, then run once with everything frozen at tag `eval-freeze-1` (`results/heldout/RUN.txt`). 15 planted flaws, 17 clean runs, 29 runs in all.

| Tool | Kind | Recall | Precision | False alarms | False-alarm rate | Extra findings | Not checkable | Probe errors | needs_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Our tool | executed | 12/15 (0.80) | 12/30 (0.40) | 11 | 6/17 (0.35) | 7 | 0 | 6 | 1 |
| Supabase advisors | reported, not executed | 8/15 (0.53) | 8/17 (0.47) | 7 | 7/17 (0.41) | 2 | 0 | 0 | 0 |
| rlsautotest | reported, not executed | 6/15 (0.40) | 6/22 (0.27) | 11 | 11/17 (0.65) | 5 | 0 | 0 | 0 |
| pgrls | reported, not executed | 2/15 (0.13) | 2/15 (0.13) | 7 | 6/17 (0.35) | 6 | 0 | 0 | 0 |
| Semgrep | reported, not executed | 0/15 (0.00) | n/a | 0 | 0/17 (0.00) | 0 | 0 | 0 | 0 |

Recall is planted flaws found over planted flaws. Precision is proved findings that match a planted flaw over all proved findings. False alarms are proved findings on clean runs (fixed twins, decoys, clean apps); the rate is clean runs with at least one false alarm over clean runs. Extra findings are unmatched proved findings on flawed runs. `n/a` means a zero denominator.

Raw outputs: our tool in `results/heldout/` (one JSON run object per run, table in `results/heldout/score.txt`); each baseline in `results/baselines/heldout/<tool>/` (raw tool output in `raw/`, run objects beside it, table in `results/baselines/heldout/score-<tool>.txt`). Versions and commit: `results/heldout/RUN.txt`.

What the numbers show, and no more:

- Our tool has the highest recall on this benchmark: 12 of 15, against 8 of 15 for the next tool.
- Its precision (12/30 (0.40)) and false-alarm rate (6/17 (0.35)) are in the same range as the others (precision 0.13 to 0.47, false-alarm rate 0.35 to 0.65; Semgrep is left out of both ranges because it reports nothing).
- 6 of its runs ended with a probe error. Each is a miss, not a finding.

### Held-out set: named items

Every item below is a line of the scorer's output for that tool. Missed means a planted flaw with no matching proved finding.

#### Held-out set: Our tool

- Missed: library-fines/vulnerable: U1 on function fee_total
- Missed: plant-swaps/vulnerable: R7 on table swap_offers
- Missed: trailhead-profiles/vulnerable: C1 on table member_profiles, column is_staff
- Extra findings: circle-directory/vulnerable: R1 on table circle_members
- Extra findings: circle-directory/vulnerable: R2 on table circle_members
- Extra findings: kiln-bookings/vulnerable: R2 on table kiln_bookings
- Extra findings: pantry-share/vulnerable: R1 on table pantry_items
- Extra findings: pantry-share/vulnerable: R2 on table pantry_items
- Extra findings: plant-swaps/vulnerable: R1 on table swap_offers
- Extra findings: plant-swaps/vulnerable: R2 on table swap_offers
- False alarms: barn-rotas/migrations: R2 on table shift_notes
- False alarms: barn-rotas/migrations: U1 on function is_team_member
- False alarms: kiln-bookings/fixed: R2 on table kiln_bookings
- False alarms: orbit-tasks/migrations: R2 on table tasks
- False alarms: orbit-tasks/migrations: U2 on function is_admin
- False alarms: pantry-share/fixed: R1 on table pantry_items
- False alarms: pantry-share/fixed: R2 on table pantry_items
- False alarms: plant-swaps/fixed: R1 on table swap_offers
- False alarms: plant-swaps/fixed: R2 on table swap_offers
- False alarms: rind-recipes/migrations: R1 on table recipes
- False alarms: rind-recipes/migrations: R2 on table recipes
- needs_decision: launch-waitlist/migrations: R3 on table waitlist_entries

#### Held-out set: Supabase advisors

- Missed: circle-directory/vulnerable: C2 on table circle_members, column contact_phone
- Missed: ferry-boarding/vulnerable: R2 on table boarding_passes
- Missed: harbor-helpdesk/vulnerable: R3 on table support_requests
- Missed: plant-swaps/vulnerable: R7 on table swap_offers
- Missed: quill-journal/vulnerable: R2 on table journal_entries
- Missed: trailhead-profiles/vulnerable: C1 on table member_profiles, column is_staff
- Missed: ward-credits/vulnerable: U2 on function admin_grant_credits
- Extra findings: kiln-bookings/vulnerable: R7 on table kiln_bookings
- Extra findings: ward-credits/vulnerable: U1 on function admin_grant_credits
- False alarms: barn-rotas/migrations: U1 on function is_team_member
- False alarms: lantern-budgets/migrations: U1 on function rename_budget
- False alarms: launch-waitlist/migrations: R3 on table waitlist_entries
- False alarms: library-fines/fixed: U1 on function fee_total
- False alarms: loyalty-punch/fixed: U1 on function spend_points
- False alarms: orbit-tasks/migrations: U1 on function is_admin
- False alarms: ward-credits/fixed: U1 on function admin_grant_credits

#### Held-out set: rlsautotest

- Missed: circle-directory/vulnerable: C2 on table circle_members, column contact_phone
- Missed: ferry-boarding/vulnerable: R2 on table boarding_passes
- Missed: harbor-helpdesk/vulnerable: R3 on table support_requests
- Missed: kiln-bookings/vulnerable: R5 on table kiln_bookings
- Missed: library-fines/vulnerable: U1 on function fee_total
- Missed: pantry-share/vulnerable: R6 on table pantry_items
- Missed: plant-swaps/vulnerable: R7 on table swap_offers
- Missed: trailhead-profiles/vulnerable: C1 on table member_profiles, column is_staff
- Missed: ward-credits/vulnerable: U2 on function admin_grant_credits
- Extra findings: circle-directory/vulnerable: R2 on table circle_members
- Extra findings: kiln-bookings/vulnerable: R2 on table kiln_bookings
- Extra findings: pantry-share/vulnerable: R1 on table pantry_items
- Extra findings: plant-swaps/vulnerable: R2 on table swap_offers
- Extra findings: ward-credits/vulnerable: U1 on function admin_grant_credits
- False alarms: barn-rotas/migrations: U1 on function is_team_member
- False alarms: circle-directory/fixed: R2 on table circle_members
- False alarms: kiln-bookings/fixed: R2 on table kiln_bookings
- False alarms: lantern-budgets/migrations: U1 on function rename_budget
- False alarms: launch-waitlist/migrations: R3 on table waitlist_entries
- False alarms: library-fines/fixed: U1 on function fee_total
- False alarms: loyalty-punch/fixed: U1 on function spend_points
- False alarms: orbit-tasks/migrations: U1 on function is_admin
- False alarms: pantry-share/fixed: R1 on table pantry_items
- False alarms: plant-swaps/fixed: R2 on table swap_offers
- False alarms: ward-credits/fixed: U1 on function admin_grant_credits

#### Held-out set: pgrls

- Missed: circle-directory/vulnerable: C2 on table circle_members, column contact_phone
- Missed: expense-claims/vulnerable: V1 on table claim_overview
- Missed: ferry-boarding/vulnerable: R2 on table boarding_passes
- Missed: harbor-helpdesk/vulnerable: R3 on table support_requests
- Missed: kiln-bookings/vulnerable: R5 on table kiln_bookings
- Missed: library-fines/vulnerable: U3 on function fee_total
- Missed: library-fines/vulnerable: U1 on function fee_total
- Missed: loyalty-punch/vulnerable: U1 on function spend_points
- Missed: pantry-share/vulnerable: R6 on table pantry_items
- Missed: plant-swaps/vulnerable: R7 on table swap_offers
- Missed: quill-journal/vulnerable: R2 on table journal_entries
- Missed: trailhead-profiles/vulnerable: C1 on table member_profiles, column is_staff
- Missed: ward-credits/vulnerable: U2 on function admin_grant_credits
- Extra findings: circle-directory/vulnerable: R1 on table circle_members
- Extra findings: kiln-bookings/vulnerable: R4 on table kiln_bookings
- Extra findings: kiln-bookings/vulnerable: R1 on table kiln_bookings
- Extra findings: pantry-share/vulnerable: R1 on table pantry_items
- Extra findings: plant-swaps/vulnerable: R1 on table swap_offers
- Extra findings: quill-journal/vulnerable: R1 on table journal_entries
- False alarms: circle-directory/fixed: R1 on table circle_members
- False alarms: expense-claims/fixed: R1 on table claim_overview
- False alarms: kiln-bookings/fixed: R1 on table kiln_bookings
- False alarms: launch-waitlist/migrations: R4 on table waitlist_entries
- False alarms: launch-waitlist/migrations: R3 on table waitlist_entries
- False alarms: pantry-share/fixed: R1 on table pantry_items
- False alarms: plant-swaps/fixed: R1 on table swap_offers

#### Held-out set: Semgrep

- Missed: circle-directory/vulnerable: C2 on table circle_members, column contact_phone
- Missed: expense-claims/vulnerable: V1 on table claim_overview
- Missed: ferry-boarding/vulnerable: R1 on table boarding_passes
- Missed: ferry-boarding/vulnerable: R2 on table boarding_passes
- Missed: harbor-helpdesk/vulnerable: R3 on table support_requests
- Missed: harbor-helpdesk/vulnerable: R4 on table support_requests
- Missed: kiln-bookings/vulnerable: R5 on table kiln_bookings
- Missed: library-fines/vulnerable: U3 on function fee_total
- Missed: library-fines/vulnerable: U1 on function fee_total
- Missed: loyalty-punch/vulnerable: U1 on function spend_points
- Missed: pantry-share/vulnerable: R6 on table pantry_items
- Missed: plant-swaps/vulnerable: R7 on table swap_offers
- Missed: quill-journal/vulnerable: R2 on table journal_entries
- Missed: trailhead-profiles/vulnerable: C1 on table member_profiles, column is_staff
- Missed: ward-credits/vulnerable: U2 on function admin_grant_credits

## Dev set

Self-check only, never quoted as accuracy: the tool and these apps were built together. 22 planted flaws, 21 clean runs, 36 runs in all.

| Tool | Kind | Recall | Precision | False alarms | False-alarm rate | Extra findings | Not checkable | Probe errors | needs_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Our tool | executed | 22/22 (1.00) | 22/22 (1.00) | 0 | 0/21 (0.00) | 0 | 0 | 0 | 3 |
| Supabase advisors | reported, not executed | 11/22 (0.50) | 11/14 (0.79) | 1 | 1/21 (0.05) | 2 | 0 | 0 | 0 |
| rlsautotest | reported, not executed | 8/22 (0.36) | 8/14 (0.57) | 4 | 4/21 (0.19) | 2 | 0 | 0 | 0 |
| pgrls | reported, not executed | 5/22 (0.23) | 5/11 (0.45) | 3 | 3/21 (0.14) | 3 | 0 | 0 | 0 |
| Semgrep | reported, not executed | 0/22 (0.00) | n/a | 0 | 0/21 (0.00) | 0 | 0 | 0 | 0 |

Recall is planted flaws found over planted flaws. Precision is proved findings that match a planted flaw over all proved findings. False alarms are proved findings on clean runs (fixed twins, decoys, clean apps); the rate is clean runs with at least one false alarm over clean runs. Extra findings are unmatched proved findings on flawed runs. `n/a` means a zero denominator.

Raw outputs: our tool in `results/devset/` (table in `results/devset-score.txt`); each baseline in `results/baselines/devset/<tool>/` (raw tool output in `raw/`, table in `results/baselines/devset/score-<tool>.txt`).

This table is a self-check that the tool works on the apps it was built against. It says nothing about how it does on other apps.

### Dev set: named items

Every item below is a line of the scorer's output for that tool. Missed means a planted flaw with no matching proved finding.

#### Dev set: Our tool

- needs_decision: columns-03-phone-exposed/vulnerable: R1 on table directory
- needs_decision: decoy-01-public-posts/migrations: R1 on table posts
- needs_decision: decoy-02-public-profile-read/migrations: R1 on table profiles_public

#### Dev set: Supabase advisors

- Missed: columns-01-self-admin/vulnerable: C1 on table members, column role
- Missed: columns-02-self-paid/vulnerable: C1 on table accounts, column paid
- Missed: columns-03-phone-exposed/vulnerable: C2 on table directory, column phone
- Missed: functions-01-admin-delete-any-user/vulnerable: U2 on function admin_delete_user
- Missed: rows-01-profiles/vulnerable: R2 on table profiles
- Missed: rows-01-profiles/vulnerable: R3 on table profiles
- Missed: rows-01-profiles/vulnerable: R4 on table profiles
- Missed: rows-01-profiles/vulnerable: R5 on table profiles
- Missed: rows-01-profiles/vulnerable: R6 on table profiles
- Missed: rows-01-profiles/vulnerable: R7 on table profiles
- Missed: rows-02-profiles-all-authenticated/vulnerable: R2 on table profiles
- Extra findings: functions-01-admin-delete-any-user/vulnerable: U1 on function admin_delete_user
- Extra findings: functions-03-default-execute/vulnerable: U1 on function note_count
- False alarms: functions-02-security-definer-no-check/fixed: U1 on function set_note_body

#### Dev set: rlsautotest

- Missed: columns-01-self-admin/vulnerable: C1 on table members, column role
- Missed: columns-02-self-paid/vulnerable: C1 on table accounts, column paid
- Missed: columns-03-phone-exposed/vulnerable: C2 on table directory, column phone
- Missed: functions-01-admin-delete-any-user/vulnerable: U2 on function admin_delete_user
- Missed: rows-01-profiles/vulnerable: R2 on table profiles
- Missed: rows-01-profiles/vulnerable: R3 on table profiles
- Missed: rows-01-profiles/vulnerable: R4 on table profiles
- Missed: rows-01-profiles/vulnerable: R5 on table profiles
- Missed: rows-01-profiles/vulnerable: R6 on table profiles
- Missed: rows-01-profiles/vulnerable: R7 on table profiles
- Missed: writes-03-update-others/vulnerable: R5 on table notes
- Missed: writes-03-update-others/vulnerable: R7 on table notes
- Missed: writes-04-delete-others/vulnerable: R6 on table notes
- Missed: writes-05-owner-change/vulnerable: R7 on table notes
- Extra findings: columns-03-phone-exposed/vulnerable: R1 on table directory
- Extra findings: functions-01-admin-delete-any-user/vulnerable: U1 on function admin_delete_user
- False alarms: columns-03-phone-exposed/fixed: R1 on table directory
- False alarms: decoy-01-public-posts/migrations: R1 on table posts
- False alarms: decoy-02-public-profile-read/migrations: R1 on table profiles_public
- False alarms: functions-02-security-definer-no-check/fixed: U1 on function set_note_body

#### Dev set: pgrls

- Missed: columns-01-self-admin/vulnerable: C1 on table members, column role
- Missed: columns-02-self-paid/vulnerable: C1 on table accounts, column paid
- Missed: columns-03-phone-exposed/vulnerable: C2 on table directory, column phone
- Missed: functions-01-admin-delete-any-user/vulnerable: U2 on function admin_delete_user
- Missed: functions-02-security-definer-no-check/vulnerable: U1 on function set_note_body
- Missed: functions-03-default-execute/vulnerable: U3 on function note_count
- Missed: rows-01-profiles/vulnerable: R2 on table profiles
- Missed: rows-01-profiles/vulnerable: R3 on table profiles
- Missed: rows-01-profiles/vulnerable: R4 on table profiles
- Missed: rows-01-profiles/vulnerable: R5 on table profiles
- Missed: rows-01-profiles/vulnerable: R6 on table profiles
- Missed: rows-01-profiles/vulnerable: R7 on table profiles
- Missed: rows-02-profiles-all-authenticated/vulnerable: R2 on table profiles
- Missed: views-01-bypass/vulnerable: V1 on table all_notes
- Missed: views-02-matview-leak/vulnerable: V1 on table all_notes
- Missed: writes-03-update-others/vulnerable: R5 on table notes
- Missed: writes-04-delete-others/vulnerable: R6 on table notes
- Extra findings: columns-03-phone-exposed/vulnerable: R1 on table directory
- Extra findings: rows-02-profiles-all-authenticated/vulnerable: R1 on table profiles
- Extra findings: writes-01-visitor-insert/vulnerable: R4 on table notes
- False alarms: columns-03-phone-exposed/fixed: R1 on table directory
- False alarms: decoy-01-public-posts/migrations: R1 on table posts
- False alarms: decoy-02-public-profile-read/migrations: R1 on table profiles_public

#### Dev set: Semgrep

- Missed: columns-01-self-admin/vulnerable: C1 on table members, column role
- Missed: columns-02-self-paid/vulnerable: C1 on table accounts, column paid
- Missed: columns-03-phone-exposed/vulnerable: C2 on table directory, column phone
- Missed: functions-01-admin-delete-any-user/vulnerable: U2 on function admin_delete_user
- Missed: functions-02-security-definer-no-check/vulnerable: U1 on function set_note_body
- Missed: functions-03-default-execute/vulnerable: U3 on function note_count
- Missed: rows-01-profiles/vulnerable: R1 on table profiles
- Missed: rows-01-profiles/vulnerable: R2 on table profiles
- Missed: rows-01-profiles/vulnerable: R3 on table profiles
- Missed: rows-01-profiles/vulnerable: R4 on table profiles
- Missed: rows-01-profiles/vulnerable: R5 on table profiles
- Missed: rows-01-profiles/vulnerable: R6 on table profiles
- Missed: rows-01-profiles/vulnerable: R7 on table profiles
- Missed: rows-02-profiles-all-authenticated/vulnerable: R2 on table profiles
- Missed: views-01-bypass/vulnerable: V1 on table all_notes
- Missed: views-02-matview-leak/vulnerable: V1 on table all_notes
- Missed: writes-01-visitor-insert/vulnerable: R3 on table notes
- Missed: writes-02-spoofed-owner/vulnerable: R4 on table notes
- Missed: writes-03-update-others/vulnerable: R5 on table notes
- Missed: writes-03-update-others/vulnerable: R7 on table notes
- Missed: writes-04-delete-others/vulnerable: R6 on table notes
- Missed: writes-05-owner-change/vulnerable: R7 on table notes

## Limits

- What the tool cannot test is listed in `docs/EVALUATION.md` section 8 (views over several tables or in other schemas, writes beyond the first two seeded users, columns with unlisted names, functions outside `public`, intent). A flaw outside those limits is a miss and stays in the totals.
- A baseline finding is labelled `proved` only so the scorer will count it (`docs/baselines.md` section 3.1). It is not proof that anyone ran the attack. Baselines are `reported, not executed`.

## Threats to validity

- We wrote the answer key, the flaw ids, the scoring rules and the mapping rules for the baselines. A different author could score differently.
- Baselines are scored as proved although they only report. This favours them on recall and counts their unconfirmed reports against their precision.
- Semgrep finds nothing because no published rule matches SQL. This says nothing about Semgrep on other languages.
- The Supabase advisors and pgrls are linters. Here they are judged as exploit finders, which is not their purpose.
- The held-out set is small: 15 planted flaws. One flaw changes recall by about 7 points.
- The held-out author knew our flaw catalogue, so the apps may lean towards flaws our tool was designed to find.
- The dev set is a self-check, never accuracy.

## How to check by hand

Pick an app and a side (`vulnerable`, `fixed`, or `migrations` for an app with no twin). Then:

1. The key entry: open `heldout/answer_key.json` (held-out apps) or `planted/answer_key.json` (dev apps) and find the app's name. `flaws_vulnerable` is what must be found on the `vulnerable` side; `flaws_fixed` and the decoy entries must give nothing.
2. Our tool, run object: `results/heldout/<app>__<side>.json` or `results/devset/<app>__<side>.json`. Each finding has a `status`, a `flaw_id`, a `table`, `column` or `function`, and its `proof` (the statement that was run and the rows seen). For our tool this file is also the raw output.
3. A baseline, raw output: `results/baselines/<set>/<tool>/raw/<app>__<side>.json` (`.csv` for the advisors), where `<set>` is `heldout` or `devset`. Find the line that names the rule.
4. A baseline, run object: `results/baselines/<set>/<tool>/<app>__<side>.json`. Each finding there must trace to a raw line through the mapping table in `docs/baselines.md` section 3.
5. Match a finding to the key by the rule in `docs/EVALUATION.md` section 3: same app, side, flaw id and target. Count again from the run objects and compare with the table and with the `score` files named under it.

To re-score everything at once: `pytest tests/test_results_table.py -v`.
