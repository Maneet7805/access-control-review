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
