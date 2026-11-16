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
- 2026-11-14, M3.6 view that bypasses row security (V1). Options and picks:
  - Source: Supabase pages "Row Level Security" (sections "Views and RLS", "Expose a view safely") and "Views" ("View security"), read in full. They say a view runs with its owner's rights, so it skips the table's row security; the fix is `security_invoker = true` (Postgres 15 and above), or on older versions revoke anon and authenticated or use an unexposed schema.
  - What proves V1: as the first test user, read the view and read the table under it. Proved when a view row matches no row of the table read. Picked over "view owner bypasses row security" (a guess from catalog flags) because execution decides.
  - Limits: only views over exactly one table in public; computed columns are ignored; a view sharing no column with its table is not compared; only the first test user is tested, not visitors; views in other schemas are not listed; materialized views are not listed. A table read that was refused counts as "shows this user no rows".
  - Key: action `read_view` (not `read`) so the table-read tests in test_planted.py skip this app. The planted view revokes access from anon so the finding is for user-a.
  - rows-01 and other existing apps have no views, so their CLI counts do not change.

- 2026-11-14, M3.7 functions. Options and picks:
  - What to call: every function in public (not trigger functions, not extension members) once as a visitor and once as the first test user, with one harmless value per argument type, in a savepoint inside a transaction that is rolled back, with a 10 second limit. An argument type we cannot fill gives an `error` result (listed in the report note), never a finding.
  - Proved only when the call ran. A refusal is `permission_denied`: no execute permission, or an error the function raises on purpose (SQLSTATE P0001). Limit: a P0001 raised because our dummy values were wrong looks like a refusal.
  - Flaw ids: visitor ran it, U3; user ran a function with "admin" in its name, U2; user ran any other function that runs with its owner's rights (security definer), U1. A function that runs with the caller's rights is limited by row security, so a user calling it is no finding, and a visitor calling it is `needs_decision` (it may be public on purpose).
  - One finding per function; the visitor is tried first, so U3 hides the U1 or U2 for the same function.
  - Known limit (false alarms): a security definer function that checks the caller by filtering (for example `where owner_id = auth.uid()`) runs without error and is still reported as U1. The roadmap rule "proved when the call ran" accepts this. The fixed twins here raise an error instead. Revisit in M3.8 if the clean apps trigger it.
  - Side effects that a rollback cannot undo (sequences, notifications) stay inside the throwaway container.
  - Key: new entries only for the three new apps. The allowed list names the call that must keep working; the service role is not a probe actor, so its check is in test_functions.py.

- 2026-11-14, M3.3 owner change (R7). Options and picks:
  - Deviation from the roadmap wording ("the row belongs to the attacker"): the probe sets the owner to the second test user, so the row ends up owned by someone other than the actor. The actor hands a row away. Options: change the victim's row to the actor (needs R5 first, so it hides the missing-check flaw behind another one), or hand own rows away. Picked the second: it isolates the missing `WITH CHECK` on new values. The assert is that after the update a row's owner is not the actor.
  - What to run: `UPDATE t SET owner = '<second user>'` with a literal value and no WHERE, as the first test user, rolled back. A literal needs no select policy. Rows already owned by the second user are left out, because nothing about them changed.
  - Planted flaw is `using (owner_id = auth.uid()) with check (true)`, not "no check". In Postgres an update policy with no `WITH CHECK` reuses its `USING` condition for the new row, so the owner change would be refused and nothing would be planted.
  - Side effects on other apps, expected: `rows-01` vulnerable (row security off) now shows R7 (CLI count 5 to 6), and `writes-03` vulnerable (`using (true)`, no check) shows R7 next to its planted R5. Tests updated to say so. The answer key is not changed for either (rule 12.3); both R7 entries are for a follow-up key PR.
  - Needs 2 users and an owner column, like R4. Only the first test user acts.
- 2026-11-14, M3.4 protected columns (C1). Options and picks:
  - Which columns are protected: a column is protected when one word of its name (split on underscores) is in role, roles, admin, paid, balance, credits, permissions, superuser. Picked over asking the key, because the tool must work on apps that have no key. The owner column is left out (R7 covers it).
  - Status: always `proved` when the change went through, because the column is picked by name and the test really changed it. `needs_decision` is not used. Limit: a protected column with an unlisted name (for example `tier`) is not tested.
  - What the test does: set the column to a new value (text: 'admin', then 'access-review' if a check rule refuses the first; boolean: the opposite; number: plus 1) on every row the user may update, only where the value really changes, in a transaction that is rolled back. Proved when one of the changed rows belongs to the acting user. Other users' rows are R5, not C1.
  - Fix wording and planted fixes: column-level privileges (revoke update on the table, grant update on the harmless columns), as Supabase documents for column security. Picked over a trigger because it is the simplest fix an app can copy.
  - Key: only `members.role` (columns-01) and `accounts.paid` (columns-02), each with an `update` allowed entry. Existing key entries are unchanged. No existing planted app has a protected-looking column, so no CLI counts moved.
- 2026-11-16, M3.5 private column readable by others (C2). Options and picks:
  - Which columns are private: a column is private when one word of its name (split on underscores) is in phone, mobile, ssn, passport, dob, birthdate, salary, password, secret, token. `email` and `address` are left out on purpose: they are public in many apps and already sit in older planted apps, so adding them would move old counts. Limit: a private column with an unlisted name is not tested.
  - Status: `proved` when a non-null value comes back, like C1 (name picks the column, the read really happened). `needs_decision` is not used for C2. Risk: a table that shows phone numbers on purpose is reported as proved; M3.8 decoys should check this.
  - What the test does: as a visitor, and as the first test user, `SELECT <private column>` (plus the owner column when the table has one) with no WHERE, no write. A signed-in user's own rows do not count; with no owner column, every value counts. Asking for the column alone means a column-level refusal shows as permission denied for that column.
  - Planted app `columns-03-phone-exposed`: `directory` table with no owner column, a select policy `using (true)`, so rows are public and phone is readable. Fixed twin: revoke select on the table, grant select on `id` and `display_name` only. No owner column on purpose: an owner column would add R2 (proved) for a table that is public by design.
  - Side effect on the new app, expected: the vulnerable app also shows R1 as `needs_decision` (a visitor reads a table with no owner column), as decoy-01 does. The key lists only the planted C2. R1 is not in the key because the table is public by design; scoring (M4) should treat it like the decoy case.
  - Key: only `columns-03-phone-exposed` (`C2`, `directory.phone`, visitor, action `read_column`, plus one `allowed` entry). Existing key entries are unchanged. No existing planted app has a private-looking column, so no old counts moved.
- 2026-11-16, M3.8 decoys and clean apps. Options and picks:
  - Layout: one `migrations/` folder per app, like decoy-01 (no vulnerable/fixed pair), because none has a planted flaw. Existing tests that loop over vulnerable/fixed folders skip them.
  - decoy-02 is a public profile table with no owner column and no private-named column, readable by anon and authenticated. Result: R1 `needs_decision`. An owner column would make R2 proved, which the tool cannot tell from a real leak (see rows-02), so the decoy has none.
  - decoy-03 is a team table shared on purpose (a membership table private to each user, notes readable by team members, no owner column on notes). Result: no finding at all, not `needs_decision`. The tool only asks for a decision when a visitor can read a table; here visitors are refused, so there is nothing to ask. The roadmap says decoys give `needs_decision`; this one gives silence, which still means no `proved`.
  - clean-01 has full own-row policies for select, insert, update and delete. clean-02 uses one `for all` policy, the cached `(select auth.uid())` form, a `security_invoker` view and a function that runs with the caller's rights, execute removed from visitors.
  - Key: four entries, no flaws, `decoy` true for the two decoys. Only `read` allowed entries, so the table-specific loops in older tests skip them. No existing entry or count changed.
  - Known gap, not fixed here: a decoy table that exposes a private-named column (for example phone) on purpose would still be `proved` C2, because the tool cannot see intent. Left as is; changing C2 status is a rule change for its own PR.
- Sandbox cleanup (fix): `_remove()` uses `docker rm -fv`. Plain postgres:16 declares an anonymous data volume that `rm -f` leaves behind (3 of 3 runs leaked one; with -v, 0 of 3). The Supabase image did not leak. Existing leaked volumes are left for the owner to prune.
