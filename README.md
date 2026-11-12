# access-control-review

Finds broken access control in apps built with AI tools such as Lovable, Bolt, Cursor and Claude Code.

Broken access control means one user can read or change another user's data, or run an action meant for admins. AI app builders often get this wrong, and the developer may not know enough to notice.

This is a final year project (CT052-3-3-INV). It is a prototype, not a finished tool.

## How it works

The tool does not guess. It rebuilds the app's database in a throwaway copy, attacks it, and reports only what it proved.

1. **Rebuild.** Create a fresh PostgreSQL database in Docker from the app's migration files.
2. **Attack.** Try to read and change data as a visitor, then as different signed-in users.
3. **Decide.** The result of each attack decides the finding. A language model never does.
4. **Report.** Each finding comes with proof, a plain-language explanation and a suggested fix. The tool never edits your code.

It never touches a live system. It can only say "no violation found under this test", never "this app is secure".

## What works today

- Rebuild a database in Docker from migration files, then delete it.
- Two attacks on rows: read as a visitor, read as a signed-in user.
- Two test apps with a planted flaw, each with a fixed twin.

Planted apps are small apps where the flaw is put in on purpose, so the right answer is known. `planted/answer_key.json` records it, and the tests check that the tool agrees.

| App | Flaw | Visitor sees rows | User A sees user B's rows |
| --- | --- | --- | --- |
| `rows-01-profiles` | Row level security is off | yes | yes |
| `rows-02-profiles-all-authenticated` | Policy lets every signed-in user read every row | no | yes |

Each fixed twin shows a visitor nothing, and shows user A only their own row.

## What is planned

- Attacks on writing rows, on columns, and on database functions and Edge Functions.
- Findings with proof, plain-language explanations and fixes.
- Scoring against other tools (Semgrep and the Supabase linter) on the same apps.
- A model that only words questions for the developer, a GitHub Action, and a small web page.

Supabase and PostgreSQL come first.

## Run the tests

You need Python 3.11 or newer and Docker running.

```bash
python -m venv .venv
.venv/Scripts/activate        # on macOS or Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

The tests start and delete real Docker containers, so the first run downloads the `postgres:16` image.

## Scope

Access control only: OWASP Top 10:2025 A01 and OWASP API Security Top 10:2023 API1, API3 and API5, checked on rows, fields and functions.

Not in scope: injection, secrets, dependencies, authentication settings, mobile apps.

## Project layout

- `src/access_review/` is the tool.
- `planted/` holds the apps with a known flaw and the answer key.
- `tests/` holds the pytest checks.
- `CODING.md` has the coding rules. Every pull request must pass tests, lint, a security scan, CodeQL and a secret scan.

## Security

Report a problem privately. See [SECURITY.md](SECURITY.md).

## Licence

MIT. See [LICENSE](LICENSE).
