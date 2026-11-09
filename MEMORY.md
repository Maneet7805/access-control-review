# MEMORY.md

Session state only: where we stopped and why. Project facts and decisions live in Notion. Read this at the start of a session. Update it at the end of one.

## Now

Setup phase. No code yet. Repo, CLAUDE.md and tooling are being set up.

## Next

1. Fill in `docs/PRD.md` from Chapter 1 section 1.5 in Notion.
2. Confirm the first stack (Supabase and PostgreSQL), including whether a lighter database setup works.
3. Install Docker (needs WSL2 on Windows), one step at a time.
4. Decide whether to disable unused plugins (caveman, GitHub plugin, design plugins).

## Open questions

- Is the first stack Supabase and PostgreSQL, or something lighter?
- Which web framework, and when?
- Which baseline tool does the supervisor want compared?
- Memory tool: Notion only, or graphify later?

## Decisions waiting to be logged in Notion

- Repo is public.
- Repo name is `access-control-review`.
- First version covers both database functions and Edge Functions.
- ECC is skipped. BMAD is skipped unless it stops competing with the current setup.

## Session log

### 2026-11-09
- Created the public repo with README, LICENSE, .gitignore and a secret-scan workflow.
- Merged CLAUDE.md (PR #1). Rewrote it from the user's own earlier CLAUDE.md files in PR #2.
- Hardened user settings: narrower read access, credential files hidden, merge and repo delete blocked.
- Reviewed ECC and the user's starred repos. Installed academic-research-skills after reading its hooks.
- Open at end: PR #2 not merged, MEMORY.md not merged, plugin trim not decided.

<!-- ANCHOR:session-log -->
