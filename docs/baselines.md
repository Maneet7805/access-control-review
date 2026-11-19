# Baselines

The other tools we compare against, how each one is run, and how its output becomes a score. This file is committed before any baseline is run on the held-out set. After that run the choice in section 1 cannot change (ROADMAP M5.5).

Sections 2 ("Commands") and 3 ("Mapping rules") were added in task M5.2.

## 1. Choice

Decision D4, recorded in task M5.1, on 2026-11-19. Nothing was installed or run to make this choice. Every fact below comes from the project's own pages, read on that date. Where a page is silent the cell says "not stated", and that is treated as unproven, never as a yes.

### Rules applied

1. A baseline must be free, must need no account, and must run locally with no network once installed (ROADMAP D4).
2. The set must include Semgrep, the Supabase advisors and at least one execution-based database tool (one that runs statements against a database).
3. Semgrep and the Supabase advisors are required by D4, so they are kept even where a page does not state that a run works offline. For them "not stated" becomes a check that M5.2 must pass. If it fails, M5.2 stops and asks.
4. Any other candidate is `Included` only if a page we read says it runs without a network or an account, and `Dropped` otherwise.
5. "Covers" lists the Appendix A flaw ids the tool could report, judged from its pages only. It is a hypothesis for M5.2, not a result. A tool that has nothing for a flaw id finds nothing there, and that is the result.

### Table

| Tool | Version | Licence | How it runs | Offline | Covers | Kind | Decision | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Semgrep | 1.186.0 (PyPI) | Engine LGPL-2.1. Registry rules: Semgrep Rules License v1.0 (own internal use, no redistribution) | `pipx install semgrep`, then `semgrep scan --config <rule file> <folder>` over the migration files | Not stated for a whole scan. With local rule files it sends no metrics. Registry rules need a download | Unknown. SQL is not on the supported-languages page, only the text-only "Generic" mode. Possible: R1, R2, U1 if a published rule matches SQL text | Static | Included | Required by D4. Free, no account for `semgrep scan`. M5.2 must show it runs with the network off and say what published rules fire on SQL, which may be none |
| Supabase advisors | No release number read. The checks are the lints 0001 to 0032 on the Advisors page; pin the lint file by commit in M5.2 | Lint file (splinter): PostgreSQL License | `psql -f splinter.sql` against a Postgres database. Other routes: `supabase db advisors` (local database by default), Studio, MCP, Management API | Not stated. The lint file is one SQL query run by the database | R1, R2 (RLS off, always-true policy), V1 (definer view, materialized view in API), U1 and U3 (definer function runnable by anon or signed-in users), C2 (sensitive column names). From lint titles only | Execution-based, but it runs read-only catalog queries, not attacks | Included | Required by D4. The lint file is free and needs no account. The Studio, MCP and Management API routes are on a Supabase project, which needs an account, so they are not used |
| rlsautotest | 0.7.1 (PyPI) | Apache-2.0 | `pip install rlsautotest`, then `rlsautotest --db-url <url> --schema public --report-json` | Yes. The PyPI page says its helper shim "runs online or air-gapped". No account stated | R1, R2, R3, R5, R6 (per identity, per command access matrix). R4, R7 via WITH CHECK checks. C1 only as a column grant that leaks. V1, U1 as review flags | Execution-based (seeds rows and runs SELECT, INSERT, UPDATE, DELETE, each rolled back) | Included | The execution-based database tool. Free, Apache-2.0, offline use stated. Asks for a throwaway copy of the database, which the sandbox is |
| pgrls | 0.57.1 (PyPI) | MIT | `pip install pgrls`, then `pgrls lint --sql-file <file> --format json` | Yes. The PyPI page says it parses DDL offline, with no Postgres and no container. No account stated | R1, R2, R4 (verify modes anon, cross-tenant, write). V1 (reachability mode and view rules). C2 (sensitive column names). U1 partly (definer function rules) | Static (reads files or the catalog; its optional probe mode runs statements) | Included | Free, MIT, offline use stated, and it reads migration files directly. Adds a static row and view checker next to Semgrep |
| rlsgrid | 0.5.7 (PyPI) | MIT | `pip install rlsgrid`, then `rlsgrid check` with `DATABASE_URL` set | Not stated. No account stated | R2, R4, R5, R6 (cross-tenant fuzz of read, insert, update, delete). R7 possible | Execution-based (seeds synthetic tenants and attacks them) | Dropped | Offline use is not stated on its page, so rule 4 is not met. Its model is cross-tenant isolation set up in a config; our apps are per-user, so the fit is unproven |
| SupaShield | 0.2.1 (package.json on the repo main branch; the npm page could not be opened) | MIT | `npm install -g supashield`, then `supashield test` with `SUPASHIELD_DATABASE_URL` set | Not stated. No account stated. The README example is a hosted-project connection string | R1, R2, R3, R5, R6 (anonymous and signed-in CRUD tests). Static lint of policies | Execution-based (rolled-back transactions), plus a static lint | Dropped | Offline use is not stated, the project website that holds the full documentation could not be opened, and the published version could not be confirmed, so rule 4 is not met |

### What was read for each tool

Each page was read in full unless noted. One line at most is quoted per page.

- Semgrep.
  - Project and install: docs page "Local scans with Semgrep". It says `semgrep scan` is for "scanning a project when you don't have a Semgrep account", and `semgrep ci` needs a login. Version and engine licence: the PyPI page and the repo LICENSE (LGPL-2.1, first lines read).
  - Run: docs page "Run rules" (local rule files with `--config PATH`; `--config=auto` and registry rulesets).
  - Network: docs page "Semgrep metrics". It says "Semgrep does not enable metrics when running with only local configuration files or command-line search patterns." Registry rules do enable metrics and must be downloaded.
  - Languages: docs page "Supported languages". SQL does not appear in it.
  - Rules licence: the rules licence page v1.0, read in full. It allows use "only for your own internal business purposes" and does not allow distributing the rules.
- Supabase advisors.
  - Project page: docs page "Advisors" (the 0001 to 0032 check list, and the four ways to run them). Lint file: README of the splinter repository ("Splinter maintains a set of lints for Supabase projects"), LICENSE (PostgreSQL License, first lines read).
  - Run: the same README ("a single query ... splinter.sql"), and the CLI reference section for `supabase db advisors` ("Inspects the local database by default"). The lint bodies themselves were not read in this task; M5.2 reads them before writing mapping rules.
  - Not stated on any of these pages: whether the local CLI route needs a login, and whether the lint file used by Studio at a given date equals the file in the repository.
- rlsautotest.
  - Project, run and licence: the PyPI page and the INSTALL.md file in the repository, both in full, and the start of the repository LICENSE (Apache-2.0). The repository LICENSE page did not render its body, so its text was checked from the raw file.
  - A related blog post by the author was read for the problem statement only.
- pgrls.
  - Project, install and run: the PyPI page, read as far as the lint, fix, generate, report, matrix and verify sections and then searched for network, account, telemetry and paid terms in the rest (about 73,000 characters of rule reference). No such statement was found. The rule reference tail was not read line by line.
  - Licence: repository LICENSE (MIT, first lines read).
- rlsgrid.
  - Project, install, run and safety notes: the PyPI page in full. Licence: repository LICENSE (MIT, first lines read). The `docs/RECIPES.md` file it links to was not read.
- SupaShield.
  - Project, install, run: the repository README in full, and package.json. Licence: repository LICENSE (MIT, first lines read).
  - Not read: the website `supashield.app` (it could not be opened) and the npm page (the certificate was not trusted).

### How each included tool would be pointed at an app (input for M5.2)

These are plans from the pages, not tested commands. M5.2 writes and runs the exact commands.

- Semgrep. Point it at the app's `migrations` folder with local rule files and `--metrics off`. The registry rules are fetched once and then used from disk. Because of the rules licence, the rule files are not copied into this repository: M5.2 records the registry id and version of each rule and pins them, and does not commit them. If no published rule matches SQL, Semgrep finds nothing and the file says so.
- Supabase advisors. Run `splinter.sql` through `psql` inside the rebuilt sandbox database, using the same `docker exec` route as the probes (decision D2, option A). Without `pgrst.db_schemas` set, the README says the API-exposure lints cover the `public` schema only; M5.2 decides whether to set it. The Studio, MCP, Management API and `--remote` routes are not used.
- rlsautotest. It connects with a database URL, but the sandbox has no network (M1.6), so the tool cannot reach the sandbox container as it is. M5.2 must find a route that keeps the network off from the internet (for example a throwaway Postgres of the same image reachable only on the local machine) and say how it was checked. The role it connects as needs the rights its doctor command lists (SET ROLE to the client roles, CREATE on the schema).
- pgrls. Run `pgrls lint --sql-file` once per migration file, in file order, with `--format json`. This needs no database and no Docker. The page warns that rules which need live catalog state are skipped in this mode (they are listed under `skipped_rules` in the JSON), so M5.2 records which rules were skipped. The mode that builds a temporary database from the migrations needs Docker and is not used first.

### Open items M5.2 must settle

- Semgrep and the advisors must be shown to run with the network off. If either needs a network or an account, M5.2 stops and asks (ROADMAP M5.2).
- Semgrep Rules License v1.0 does not allow distributing the rules. The M5.2 plan to keep published rule files under `baselines/<tool>/` must not copy registry rules into this repository without a decision from Maneet.
- No tool has been installed, so no version, command or flaw coverage above has been run. All "Covers" cells are judgements from documentation.
- The advisors page lists lints by title. The mapping from a lint to a flaw id and a target needs the lint bodies, which M5.2 reads first.
- The tools that connect to a database may need a role with more rights than the sandbox test roles give. M5.2 records any such change in `ASSUMPTIONS.md`.

## 2. Commands

Task M5.2, 2026-11-19. Every command below was run on this machine and its raw output is saved as `tests/fixtures/baselines/<tool>/<app>__<side>.<json|csv>`. The apps are the dev apps in `planted/`: 31 vulnerable and fixed folders plus 5 decoy and clean folders, so 36 runs per tool. `hostile-01-callout` has no key entry and is not run. Nothing outside `planted/` is read.

### 2.1 One-time setup

Docker is the only requirement beyond Python. Each static tool runs inside one image so the network can be cut off and shown to be off.

```
docker build -t acr-baselines:m52 baselines/tools
git clone https://github.com/semgrep/semgrep-rules <folder>/semgrep-rules
git -C <folder>/semgrep-rules checkout a5ad1714f00c9f7fde980cab0ea1d6dc6d414fd2
```

- The image (`baselines/tools/Dockerfile`) is `python:3.12-slim` plus `semgrep==1.186.0`, `rlsautotest==0.7.1` and `pgrls==0.57.1`. It is built once with a network. Nothing is fetched when a tool runs.
- In Git Bash on Windows set `MSYS_NO_PATHCONV=1` first and write the repository folder as `$(pwd -W)`. Below, `$W` is that folder and `$RULES` is the semgrep-rules clone.
- `baselines/capture.sh` runs all four commands over every dev app and writes the fixtures. `ONLY='<regex>'` limits it to some apps.
- Rebuilt app: Supabase Postgres (`supabase/postgres:15.19.0.019`) built by the sandbox from the migration files, with `baseline.sql` and the migrations run as the `postgres` role (the sandbox's `baseline=True` mode). Semgrep and pgrls read the files and need no database.

### 2.2 Semgrep (static)

```
docker run --rm --network none -v "$W/planted:/work/planted:ro" -v "$RULES:/rules:ro" -w /work acr-baselines:m52 \
  semgrep scan --config /rules/generic --metrics off --disable-version-check --json --quiet planted/<app>/<side>/migrations
```

- Version 1.186.0. Input: the migrations folder. Output: JSON on stdout, saved as `semgrep/<app>__<side>.json`. The `time` fields change on every run, so a re-run is compared on `results`, `errors` and `paths`.
- Rules: the published `generic/` folder of the semgrep-rules repository at the pinned commit. No rule is written or edited. The pins are in `baselines/semgrep/PINS.md` and the 257 rule ids in `baselines/semgrep/rule_ids.txt`. Rule files are not in this repository (Semgrep Rules License v1.0).
- Network off: `--network none`, plus `--metrics off --disable-version-check`.
- What it finds: nothing, on any of the 36 runs. No published rule matches SQL: none of the 2155 `languages:` entries in the pinned repository names SQL. The `generic/` rules that can read a `.sql` file are secret-pattern and config rules, and none fires on the planted apps. Semgrep reports zero items on both sides of every app, and that is its result.
- Limit: only the `generic/` folder was run. Rule folders for other languages hold some `generic` or `regex` rules meant for their own file types. They were not run on `.sql` files.

### 2.3 Supabase advisors (catalog checks, read-only)

```
python baselines/advisors/run_splinter.py planted/<app>/<side>/migrations
```

- The lint file is `baselines/advisors/splinter.sql` from `supabase/splinter` at commit `cc529aa9d3eeffd2e64576c7591e60b22abd205c` (PostgreSQL License). Pins: `baselines/advisors/PINS.md`.
- The driver starts the sandbox (`sandbox(..., baseline=True)`), runs the file with `docker exec psql --csv` as `postgres`, and removes the container. Output: CSV, one row per lint hit, saved as `advisors/<app>__<side>.csv`. A file with only the header means no hit.
- These are read-only catalog queries. They are checks, not attacks. They never run a statement as a visitor or a user.
- Network off: the sandbox container is `--network none` with no capability beyond the start set. SQL goes in through `docker exec`.
- No setting is changed, so the API-exposure lints cover the `public` schema only.

### 2.4 rlsautotest (execution-based)

```
python baselines/rlsautotest/run_rlsautotest.py planted/<app>/<side>/migrations
```

- Version 0.7.1. The driver builds the same database as the sandbox (image, limits, `baseline.sql`, migrations) on a Docker network created with `--internal` and with no published port, so it cannot be reached from the internet or from the host. It then runs, in the pinned image on that network:
  `rlsautotest --db-url postgresql://postgres:<random password>@db:5432/postgres --schema public --report --report-json /tmp/r.json --no-fail --quiet`
  and prints the JSON file. The tool prints its text report and the JSON on the same stream, which is why the JSON goes to a file. The container and network are removed afterwards. The password is random per run and is not saved.
- The tool seeds rows and runs SELECT, INSERT, UPDATE and DELETE as each identity, rolled back. It runs as the `postgres` role, the role the migrations use, so it needs no right beyond the sandbox's. A superuser role was also tried on one app and tested fewer cells, so it was not used.
- Network off, checked three ways: `docker network inspect` shows `Internal=true`; the database container has no published port (`5432/tcp: null`, no port bindings); from a container on that network a connection to 1.1.1.1 gives "Network is unreachable" and a name lookup fails.
- Output: JSON, saved as `rlsautotest/<app>__<side>.json`. A re-run gives the same output.

### 2.5 pgrls (static)

```
docker run --rm --network none -v "$W/planted:/work/planted:ro" -w /work acr-baselines:m52 \
  pgrls lint --sql-file planted/<app>/<side>/migrations/<file>.sql --format json
```

- Version 0.57.1. Each dev app has exactly one migration file. Output: JSON on stdout, saved as `pgrls/<app>__<side>.json`.
- An app with several migration files is run once per `.sql` file, in file name order (the order the sandbox applies them). The outputs are merged into one run: each mapped item names its file in its proof line, two items with the same flaw id and target are one finding (3.1), and the unmapped counts add up. Every file's raw output is kept, as `<app>__<side>__<file>.json`. If any file's command fails or its output cannot be read, the whole run is `not_checkable`, never a partial result. A folder with no `.sql` file is `not_checkable`. A one-file app is unchanged.
- It reads the SQL only. 25 rules need live catalog state and are skipped in this mode: PERF003, PERF004, SEC013 to SEC017, SEC023, SEC029, SEC035, SEC041 to SEC044, SEC046 to SEC048, SEC051 to SEC054 and VIEW001 to VIEW004. They are listed in `skipped_rules` of every output. So pgrls cannot see views or definer functions, and an empty result from it is not a pass.
- Network off: `--network none`.

### 2.6 How "network off" was checked

- Semgrep and pgrls: the container is `--network none`. Inside it `/proc/net/dev` lists only `lo`, a connection to 1.1.1.1 gives "Network is unreachable" and a name lookup gives "Temporary failure in name resolution". Both tools still produced their normal output, so neither needs a network at run time.
- Advisors: the same check on the `supabase/postgres` image with `--network none` shows only `lo`. The sandbox runs the database in that mode and the lints ran in it.
- rlsautotest: see 2.4. It needs a network between the tool and the database, and that network is internal.
- No tool asked for an account or a login.

### 2.7 Negative control, per tool

Each command was re-run word for word on both sides of one dev app and compared with the saved fixture: Semgrep and pgrls on `rows-01-profiles`, advisors on `views-01-bypass`, rlsautotest on `rows-01-profiles`. All four outputs equal the fixtures.

| Tool | Vulnerable side | Fixed side | Plain result |
| --- | --- | --- | --- |
| Semgrep | no item | no item | Finds nothing on either side. See 2.2 |
| Supabase advisors | `security_definer_view` on `views-01` | no hit | Passes the control on this app. Across all apps it gives one mapped item on a fixed side (below) |
| rlsautotest | `exposed` on `rows-01` | none mapped | Passes the control on this app. Across all apps it gives mapped items on fixed or clean runs (below) |
| pgrls | `SEC001` on `rows-01` | raw output is not empty (`SEC002`, `SEC007`, `SEC022`, `PERF001`); none of it is mapped | Not empty raw, none mapped. Across all apps it gives mapped items on fixed or clean runs (below) |

Mapped items on fixed or clean runs, over all 36 runs per tool. By `docs/EVALUATION.md` these are false alarms. They are not hidden:

- advisors: `U1` on `set_note_body` for `functions-02` fixed (lint 0029: a definer function can be run by signed-in users; the lint cannot see the check inside it).
- rlsautotest: `U1` on `set_note_body` for `functions-02` fixed (same reason); `R1` on `directory` for `columns-03` fixed (open read policy); `R1` on `posts` for `decoy-01` and `R1` on `profiles_public` for `decoy-02` (public reads the key accepts).
- pgrls: `R1` on `directory` for `columns-03` fixed (`SEC038`); `R1` on `posts` for `decoy-01` and `R1` on `profiles_public` for `decoy-02`.

## 3. Mapping rules

### 3.1 What every tool shares

- A mapped finding has an app, a side, a flaw id from ROADMAP Appendix A and a target (`table`, `column` or `function`; a view is named in `table`). It is emitted with status `proved`, because the scorer counts only `proved` findings (decision confirmed by Maneet in PR 66). `docs/EVALUATION.md` is not changed.
- The results table labels baselines "reported, not executed" and our tool "executed". A baseline's `proved` is a label for the scorer. It is not evidence that the flaw was run, and the label is wording in the table, not a field in the finding.
- An item that cannot be placed in a flaw id and a target is not emitted. It is counted as unmapped and stays in the raw output. Every rule id not in a table below is unmapped.
- The table, column or function name is read where the tables say. The schema prefix `public.` and quotes are dropped. A function name is cut at the `(`.
- Two mapped items with the same flaw id and target are one finding.
- The rules come from each tool's own pages and from its output on `planted/` only. They were not checked against the held-out set and must not change once M5.4 starts.
- Where a tool says only "always-true policy", the role list in its output decides: `anon` gives the visitor flaw, signed-in roles give the signed-in flaw. Where the output has no role list, the item is unmapped.

### 3.2 Semgrep

No rule is mapped. No published rule matches SQL (2.2), so every item it could ever report is unmapped. On the dev apps it reports zero items.

### 3.3 Supabase advisors

Read from the CSV row: `name` (the lint) and the `metadata` JSON (`metadata.name` is the table, view or function).

| Lint (`name`) | Flaw | Target read from | Condition |
| --- | --- | --- | --- |
| `rls_disabled_in_public` | R1 | `metadata.name` as table | none |
| `policy_exists_rls_disabled` | R1 | `metadata.name` as table | none |
| `rls_policy_always_true` | R3 | `metadata.name` as table | `metadata.command` is INSERT and `metadata.roles` has `anon` or `public` |
| `rls_policy_always_true` | R4 | `metadata.name` as table | `command` is INSERT and the roles are signed-in only |
| `rls_policy_always_true` | R5 | `metadata.name` as table | `command` is UPDATE and `metadata.permissive_using` is true |
| `rls_policy_always_true` | R7 | `metadata.name` as table | `command` is UPDATE and `metadata.permissive_with_check` is true |
| `rls_policy_always_true` | R6 | `metadata.name` as table | `command` is DELETE and `metadata.permissive_using` is true |
| `security_definer_view` | V1 | `metadata.name` as table | none |
| `materialized_view_in_api` | V1 | `metadata.name` as table | none |
| `anon_security_definer_function_executable` | U3 | `metadata.name` as function | none |
| `authenticated_security_definer_function_executable` | U1 | `metadata.name` as function | none |
| `sensitive_columns_exposed` | C2 | `metadata.name` as table, each name in `metadata.sensitive_columns` as column | none |

Unmapped, for example: `unindexed_foreign_keys`, `auth_rls_initplan`, `rls_enabled_no_policy`, `function_search_path_mutable`, `auth_users_exposed`, `rls_policy_always_true` with command ALL or SELECT, and every other lint. The lints cannot tell U1 from U2, so U2 is never emitted. No lint speaks to C1. `sensitive_columns_exposed` did not fire on any dev app.

### 3.4 rlsautotest

Read from the JSON. The table name is `tables[].table`.

| Where in the JSON | Match | Flaw | Target |
| --- | --- | --- | --- |
| `tables[].exposed` | is true (RLS off, reachable by anon or signed-in) | R1 | `tables[].table` |
| `tables[].footguns[]` | `policy <name>: SELECT USING (true) -> every [<roles>] sees ALL rows`, roles include `anon` | R1 | `tables[].table` |
| `tables[].footguns[]` | the same text, signed-in roles only | R2 | `tables[].table` |
| `tables[].footguns[]` | `policy <name>: INSERT WITH CHECK (true) -> any [<roles>] may write any row`, roles include `anon` | R3 | `tables[].table` |
| `tables[].footguns[]` | the same text, signed-in roles only | R4 | `tables[].table` |
| `bypass_surfaces[]` | `type` is `view` or `materialized view`, and `why` says `readable by anon` or `readable by authenticated` | V1 | `object` as table |
| `bypass_surfaces[]` | `type` is `function`, and `why` says `EXECUTE-able by anon` | U3 | `object` up to the `(` as function |
| `bypass_surfaces[]` | `type` is `function`, and `why` says `EXECUTE-able by authenticated` | U1 | `object` up to the `(` as function |

Unmapped, for example: the `NOT TESTABLE` and `UPDATE not fully tested` footguns; `bypass_surfaces` of type `role` (BYPASSRLS roles) and type `table` ("RLS is enabled but not FORCED", "dual write path"); and the executed fields `idgrid` (a cell with `pass` false), `leak_cells`, `transition_leaks` and `column_security.cells[].leaked`. Those executed fields never reported a failed cell on any of the 36 dev runs, so no planted run shows what one looks like, and no rule is written from a guess. If one ever appears it is counted as unmapped. No rule emits R5, R6, R7, C1 or U2. The tool reported nothing for `writes-03`, `writes-04` and `writes-05`.

### 3.5 pgrls

Read from `violations[]`: `rule_id`, `message` and `location`. The table is the second part of `location` (`public.notes.any insert` gives `notes`).

| Rule | Title | Flaw | Condition |
| --- | --- | --- | --- |
| `SEC001` | RLS not enabled on table | R1 | none |
| `SEC038` | Anonymous read leak (USING is true for an unauthenticated session) | R1 | none |
| `SEC049` | PostgREST-exposed table readable by a low-trust role | R1 | message says `grants SELECT to anon` |
| `SEC039` | Permissive write policy grants access to the anonymous role | R3 | none |
| `SEC028` | Write-side policy WITH CHECK is constant true | R4 | none |
| `SEC006` | Write-side policy missing WITH CHECK | R7 | message says `covers UPDATE` |
| `SEC020` | Policy WITH CHECK is constant true but USING is not | R7 | none |

Unmapped, for example: `SEC008` (USING is true; the output names no role and no command, so the flaw id cannot be placed), `SEC005`, `SEC002`, `SEC007`, `SEC010`, `SEC022`, `SEC027`, `PERF001` and the 25 skipped rules (2.5). No rule emits R2, R5, R6, V1, C1, C2, U1, U2 or U3.

### 3.6 What the rules give on the dev apps

Counted from the saved fixtures with the tables above. It checks that the rules work. It is not a score: the tool and the dev set were built together, and matching against the key is the scorer's job (M5.3, M5.4).

| Tool | Flawed runs with a mapped item (of 15) | Fixed, decoy or clean runs with a mapped item (of 21) | Unmapped items, all runs |
| --- | --- | --- | --- |
| Semgrep | 0 | 0 | 0 (it reports nothing) |
| Supabase advisors | 11 | 1 | 77 |
| rlsautotest | 10 | 4 | 70 |
| pgrls | 7 | 3 | 151 |
