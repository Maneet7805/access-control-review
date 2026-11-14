# Assumptions

This file records the defaults the agent chose when Maneet had no answer, one line each.
- 13 Nov 2026: Ran the M1.1 spike without a G0 tick or D1 pick because Maneet said "You decide". D1 itself is not decided.
- 13 Nov 2026: Built M1.6 with D2 = A (probes run through `docker exec`) because Maneet said "proceed" and A is the roadmap default. D2 itself is not ticked.
- 13 Nov 2026: Added task M1.8 (demo_sandbox) so owner gate G1 can be run; no task built it. Options: add M1.8, or edit G1. Picked M1.8: smallest change. Prints counts for table `profiles` by default.
- 13 Nov 2026: M2.2 needs a JSON schema validator. Options: hand-written checks, or `jsonschema`. Picked `jsonschema` as a dev-only dependency (tests); the code itself validates in plain Python.
- 13 Nov 2026: CLI exit code is 1 only when a finding is `proved`; `needs_decision` alone exits 0 (the report still lists it). Options: fail on both. Picked the first so public-on-purpose tables do not fail a build.
- 13 Nov 2026: The CLI acts as the first 2 users already in auth.users. An app that seeds no users gets only the visitor probe. Options: insert synthetic users. Not done in M2; revisit before real apps (M7).

- 2026-11-13, M2.5 review hardening. Options seen per finding; picks and why:
  - Fewer than 2 users: print a note in the report (not exit 2). Exit 2 would block apps that are fine. Synthetic users stay future work (M7).
  - Probe name: `"public"."table"`, so a same-named schema cannot shadow the table.
  - Table and user lists: read as JSON, so a newline in a name cannot split it.
  - Report text: backticks in data are replaced. Other Markdown/HTML in names is not escaped; the web page (M9) must escape.
  - Sandbox now sends SQL as bytes. Windows text mode was adding a carriage return to every newline inside migrations.

- 2026-11-14, M3.1 insert attacks. Options and picks:
  - How to prove an insert: run it in BEGIN ... ROLLBACK and read the row back inside the same transaction (matched by its transaction id). A trigger that swallows the insert then counts as refused. Picked over counting rows, which a trigger could fool.
  - Test row: fill only columns that are required and have no default, using one harmless value per type. A required column of any other type gives an `error` result, not a finding. Limit: tables with such columns, or foreign keys other than the owner, are not tested for insert.
  - R3 on a table with no owner column is `needs_decision` (it may be a public form). With an owner column it is `proved`.
  - R4 uses the first 2 users in auth.users: the first acts, the second is the victim.
  - Key: only `notes` with an `insert` allowed entry for each new app. The read tests in test_planted.py now run only for apps whose key lists a read; write apps are covered in test_writes.py. No test was weakened.

- 2026-11-14, M3.2 update and delete. Options and picks:
  - What to run: UPDATE (one harmless column set to a fixed value) and DELETE on every row, with no WHERE, as the first test user. Picked over "WHERE owner = other user" because Postgres also applies the select policy when a WHERE reads columns, so a missing select policy would hide a real update flaw.
  - Proof: update is read back by transaction id; delete is compared before and after, all in a transaction that is rolled back (tested: data unchanged).
  - A finding is proved when any touched row is owned by someone other than the actor. Limits: a delete blocked by a foreign key, or a table with no settable column, gives an `error` result and no finding.
  - Only the first test user acts. Visitors are not tested for update or delete; R5 and R6 are about users.
- 2026-11-14, M3.2 review hardening: the update probe tries each settable column in turn; the delete diff counts identical rows one by one; a probe that ends in an error is listed in a report note, so a result is never silently clean. Ownership takeover (change the owner column) stays M3.3.

- 2026-11-14, M3.7 functions. Options and picks:
  - What to call: every function in public (not trigger functions, not extension members) once as a visitor and once as the first test user, with one harmless value per argument type, in a savepoint inside a transaction that is rolled back, with a 10 second limit. An argument type we cannot fill gives an `error` result (listed in the report note), never a finding.
  - Proved only when the call ran. A refusal is `permission_denied`: no execute permission, or an error the function raises on purpose (SQLSTATE P0001). Limit: a P0001 raised because our dummy values were wrong looks like a refusal.
  - Flaw ids: visitor ran it, U3; user ran a function with "admin" in its name, U2; user ran any other function that runs with its owner's rights (security definer), U1. A function that runs with the caller's rights is limited by row security, so a user calling it is no finding, and a visitor calling it is `needs_decision` (it may be public on purpose).
  - One finding per function; the visitor is tried first, so U3 hides the U1 or U2 for the same function.
  - Known limit (false alarms): a security definer function that checks the caller by filtering (for example `where owner_id = auth.uid()`) runs without error and is still reported as U1. The roadmap rule "proved when the call ran" accepts this. The fixed twins here raise an error instead. Revisit in M3.8 if the clean apps trigger it.
  - Side effects that a rollback cannot undo (sequences, notifications) stay inside the throwaway container.
  - Key: new entries only for the three new apps. The allowed list names the call that must keep working; the service role is not a probe actor, so its check is in test_functions.py.
