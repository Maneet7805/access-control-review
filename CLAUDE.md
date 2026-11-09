# CLAUDE.md

Project context lives in Notion, not here. Read it before planning. Start page: https://app.notion.com/p/407e14fc816e816caf34e5540d08b7e8

If this file and Notion disagree, check the page's last-edited date and ask Maneet.

## How to work

These four habits bias toward care over speed. For a trivial change, use judgment.

1. Think before coding.
   - State assumptions. If unsure, ask.
   - If a request can be read two ways, show both. Do not pick silently.
   - If a simpler way exists, say so and push back when warranted.
   - If something is unclear, stop and name what is unclear.
2. Simplicity first.
   - Write the least code that solves the problem. Nothing speculative.
   - No features, options or abstractions that were not asked for.
   - No error handling for cases that cannot happen.
   - If 200 lines could be 50, rewrite it.
3. Surgical changes.
   - Touch only what the request needs. Match the existing style.
   - Do not tidy or refactor nearby code that is not broken. Mention unrelated problems instead of fixing them.
   - Remove only what your own change made unused.
   - Every changed line should trace back to the request.
4. Goal-driven execution.
   - Turn each task into a check that can pass or fail. Fix a bug by first writing a test that fails, then make it pass.
   - For multi-step work, write a short plan where each step names how it will be verified.
   - Say what you ran and what it showed. Never report success you did not observe.

## Project rules

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
- Never merge a pull request. Maneet merges.
- Do not raise or push deadlines. Do not discuss semester 2.

## Working with Maneet

- Challenge first. Tag claims [Certain], [Likely] or [Guessing].
- Plain language, short, explain technical terms at first use.
- Ask before acting on your own. Give terminal commands one at a time (Windows PowerShell).
- Record decisions in the Decisions database in Notion, not only here.
