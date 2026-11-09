# access-control-review

A tool that reviews AI-generated web apps for broken access control, built for novice developers who use AI app builders and coding agents.

Broken access control means one user can read or change another user's data, or run an action meant for admins.

## Status

Prototyped, not built. This repository is where the real tool will be built. It is part of a final year project (CT052-3-3-INV) and is under active planning. There is no usable code yet.

## How it is meant to work

1. Read an app's repository and its database files to find the access rules.
2. Rebuild the database in an isolated copy. The tool never contacts a live system.
3. Test access as a visitor and as different signed-in users. Tests run in transactions that are rolled back.
4. Execution decides every finding. A language model never does.
5. Report each finding with proof, a plain-language explanation and a fix. The tool never edits the developer's code.

## Scope

Access control only: OWASP Top 10:2025 A01 and OWASP API Security Top 10:2023 API1, API3 and API5, checked on rows, fields and functions.

Not in scope: injection, secrets, dependencies, authentication settings, mobile apps.

The tool never claims an app is secure. It can only report "no violation found under this test".

## Licence

MIT. See [LICENSE](LICENSE).
