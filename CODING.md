# Coding

Conventions for this codebase. Short on purpose: if the code and this file disagree, fix whichever is wrong in the same change.

## Stack

- Python, with pytest for tests.
- PostgreSQL in Docker for the disposable database copy. Each review starts a fresh copy and throws it away. The first test passed on plain `postgres:16` with `anon` and `authenticated` roles created by the migration and `SET ROLE` to act as them, so that is what we use. Move to Supabase's image only when a test needs something plain PostgreSQL cannot fake.
- A local model through Ollama, only to word questions. The model is not the place where findings are decided.
- Everything else is added when the code needs it. When a test shows a choice here does not work, change it here in the same PR.

## Style

- Names: `snake_case` for functions, variables and files; `PascalCase` for classes; `SCREAMING_SNAKE` for constants. Booleans start with `is_`, `has_` or `can_`.
- A function does one thing. Past about 50 lines or 3 levels of nesting, split it. A file owns one feature.
- No magic numbers: use a named constant. No commented-out code: delete it, git keeps history.
- Comments say why, not what.
- TODO format: `# TODO(name, DD MMM YYYY): what`. A bare TODO is not allowed.
- Never disable a linter or compiler warning without a comment saying why.

## Errors

- Never swallow an error silently. Handle it, log it, or re-raise it.
- Validate at the boundary (files, SQL from reviewed repos, model replies), then trust the value downstream.
- Never log a secret.

## Tests

- Every bug fix gets a test that fails without the fix.
- Run `pytest` before every commit.

## Debugging

1. Reproduce it. If you can't, write down what you tried.
2. Reduce it to the smallest case that still fails.
3. Write down your guess at the cause before reading the suspect code.
4. Confirm the guess with a test, a log or a breakpoint. Don't assume.
5. Fix it, and add a test that fails before the fix and passes after.
6. Stuck for an hour? Stop, write down what you know, and ask the owner.

## Performance

Make it correct first. Measure before optimising.

## Commits

- Conventional Commits: `feat`, `fix`, `docs`, `test`, `chore`, with an optional scope.
- One change per PR. Never push to `main`.
- Never run a destructive command (`rm -rf`, force-push, dropping a database) without checking with the owner first.

## Layout

- `src/access_review/`: the tool. `sandbox.py` rebuilds an app's database in Docker, `probes.py` attacks it.
- `planted/`: apps with a known flaw. One folder per app named `kind-number-shortname`, each with `vulnerable/` and `fixed/` migrations, and an entry in `planted/answer_key.json`.
- `tests/`: pytest. Run `pip install -e ".[dev]"` once, then `pytest` (needs Docker running).
