# CLAUDE.md

Project context lives in Notion, not here. Read it before planning. Start page: https://app.notion.com/p/407e14fc816e816caf34e5540d08b7e8

If this file and Notion disagree, check the page's last-edited date and ask Maneet.

## Rules

- Never claim an app or the tool is "secure". Only "no violation found under this test".
- Say "developer", not "builder". Say "prototyped", never "built".
- No emojis in files or chat.
- Do not use the old working product name in this repo, the report or slides. Say "the tool".
- Real public repos that were scanned are private working material. Use cover names only (StudyLoop, CraftCrate, SimmerClub, OpenCareer, Backstop, ClinicPulse). Never commit owner names or repo URLs of scanned apps. This repo is public.
- Do not quote numbers from old notes. Only numbers produced by a run in this repo.
- No accuracy scores on real public apps. Scores come only from apps with planted flaws.
- Free or open-source tools and models only.
- The tool must never contact a live system. It treats SQL and files from other repos as untrusted and runs them only in a disposable container with no network.
- Execution decides every finding. The language model never does.
- Never commit keys, tokens or real app data.
- No Claude attribution in commits or pull requests: no Co-Authored-By line, no "Generated with" line, no session link.
- Do not raise or push deadlines. Do not discuss semester 2.

## Working with Maneet

- Challenge first. Tag claims [Certain], [Likely] or [Guessing].
- Plain language, short, explain technical terms at first use.
- Ask before acting on your own. Give terminal commands one at a time (Windows PowerShell).
- Record decisions in the Decisions database in Notion, not only here.
