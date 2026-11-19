# Semgrep pins

No rule files are stored here. The registry rules are under the Semgrep Rules License v1.0 (own internal use, no redistribution), so only the pins are kept.

- Engine: semgrep 1.186.0 (PyPI), installed by `baselines/tools/Dockerfile`.
- Rules: the public `semgrep-rules` repository (the source of the registry rules), commit `a5ad1714f00c9f7fde980cab0ea1d6dc6d414fd2` (2026-11-10), cloned on the developer's machine and mounted read-only. Used folder: `generic/`.
- `rule_ids.txt`: the id of each rule in that folder (257), in the form Semgrep prints.
- No rule in that repository at that commit names SQL as a language (0 of 2155 `languages:` entries). No custom rule is written.
