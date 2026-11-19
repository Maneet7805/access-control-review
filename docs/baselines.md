# Baselines

The other tools we compare against, how each one is run, and how its output becomes a score. This file is committed before any baseline is run on the held-out set. After that run the choice in section 1 cannot change (ROADMAP M5.5).

Sections 2 ("Commands") and 3 ("Mapping rules") are added in task M5.2.

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
