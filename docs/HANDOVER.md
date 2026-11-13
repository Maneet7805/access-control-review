# Handover for Claude Code: Maneet's final year project (FYP)

Written 9 Nov 2026. Read this whole file first. It is a map, not the full story. The full story is in Notion (section 4 below). When this file and Notion disagree, check the page's last-edited date and ask Maneet.

## 1. What this is

- Maneet (GitHub: Maneet7805) is a Computer Science student at APU (Asia Pacific University). This is his FYP, module CT052-3-3-INV. His supervisor is a lecturer at APU.
- The project is a tool that reviews AI-generated web apps for broken access control. The people it helps are novice developers who build apps with AI tools such as Lovable, Bolt, Cursor and Claude Code.
- Broken access control means one user can read or change another user's data, or run an action meant for admins.
- Report title (v3): "Enhancing Artificial Intelligence Generated Application Security for Novice Developers through Requirement Driven Execution Based Review".
- Right now he is writing the Investigation Report (IR). The tool has been prototyped, not built. Say "prototyped", never "built" or "already built".
- This repo is where the real tool gets built. He wants to start coding now, alongside Chapters 2 and 3 of the report.

## 2. What the tool does (agreed design)

1. Read the app's repository and its database files (migrations, or an export of the database structure) to find the access rules.
2. Rebuild the database in an isolated copy. It never touches a live system.
3. Test access as a visitor and as different signed-in users. Tests run in transactions that are rolled back.
4. Execution decides every finding. The language model never decides a finding.
5. Ask the developer a plain-language question only where the code cannot settle what access was intended. Example: "Should anyone be able to read this table?" This step comes later, after his survey and interview data (about December or later).
6. Report each finding with proof, a plain-language explanation and a fix. The tool never edits the developer's code. The developer gives the fix to their own AI, and the tool re-checks.
7. Delivery: a GitHub Action (an automatic check that runs when code is pushed, like CodeRabbit or a normal CI check), plus a web page. On the web page a person creates a project, adds a GitHub link or uploads a folder, and re-runs the review.

Scope is access control only: OWASP Top 10:2025 A01, and OWASP API Security Top 10:2023 API1, API3, API5. Rows, fields (columns) and functions are the three places checked. Not in scope: injection, secrets, dependencies, authentication settings, mobile apps.

Platforms: he wants the tool to cover more than Supabase (for example Firebase, or Postgres with a different login system). Decision on 30 Oct: build and test one stack first, then decide on a second once he sees his time and accuracy. The report does not state a platform count in Chapter 1. Chapter 3 will name the platforms. Which stack goes first is not yet written down in the report; Supabase's local setup is the working assumption.

Some findings are wrong in any app ("structural", for example a user making themselves admin). Others are wrong only if the developer did not intend them ("contestable", for example a table anyone can read). The report calls these requirement-independent and requirement-dependent.

## 3. Hard rules for anything you write or say

- Never claim an app or the tool is "secure". Only "no violation found under this test".
- Say "developer", not "builder".
- No emojis, in files or in chat.
- The working product name in old Notion pages is "SpecLens". Do not put it in the report or in slides. Say "the tool". Ask Maneet what to call the repo.
- Real public repos that were scanned are private working material. Use cover names only. Never put owner names or repo URLs in any file that could be committed or shared.
- Do not quote numbers from old notes. Several early figures were wrong and were corrected on 24 Oct. Only quote numbers that a run in this repo produced.
- No accuracy scores on real public apps. They are labelled case studies ("clear bug", "depends on intent", "cannot tell"). Scores come only from apps with planted flaws.
- Free or open-source tools and models only. Budget is zero.
- The tool must never contact a live system.
- Do not add Claude attribution to commits or pull requests. No "Co-Authored-By" line, no "Generated with Claude Code" line, no session link. This is set in his Claude Code settings.
- Do not raise or push deadlines. He tracks them himself.
- Do not discuss semester 2 until its guidelines are released.

## 4. Where the context lives (read in this order)

Connect Notion first. If it is not connected, ask Maneet to connect it. He is a beginner at this, so give plain step-by-step instructions that name which button to press.

1. Start here (rules for the whole workspace)
2. Chapter 1 (v3). Section 1.5 is the contract for what to build, and section 1.4 has the three objectives
3. Chapter 2 (v5). Table 2 compares 15 similar works and tools. Section 2.4 lists the technology choices, which are not final
4. Single source of truth and decision history (last updated 28 Oct, so older than the two chapters above)
5. What the tool checks, flaw by flaw
6. The tool section (prototype notes, findings tables, demo script)
7. FYP home, with the Decisions database (decision numbers like D72)

For scope and delivery, Chapters 1 and 2 are newer than the single source of truth. Write new decisions into the Decisions database in Notion, not only in chat or in this repo.

## 5. How to work with Maneet

- Challenge first. Do not open with agreement. Tell him if he is wrong, and say what you would do instead and what the risk is in his way.
- Tag claims: [Certain] for hard evidence, [Likely] for a strong inference, [Guessing] for gaps.
- If he pushes back without new information, hold your position.
- Plain language. Short by default, but keep all necessary detail. Explain any technical term in a short phrase at first use.
- Ask before acting on your own. Several past unapproved actions caused confusion.
- Give terminal commands one at a time. He uses Windows (PowerShell), Python 3.13 and Git. He works in C#/.NET, Python and TypeScript/Next.js.
- If an idea of his is hard, find a workable way to build it. Reject only if it is impossible or far too complicated. Always flag when something is impossible, paid or limited.
- Numbers he mentions are often rough working figures, not hard rules. Ask which it is.
- He wants research findings and decisions saved where he can find them, so he never repeats himself.
- Never invent facts about the project. If you do not know, ask.

## 6. Technology and environment

Chosen in Chapter 2 section 2.4 (first version, may change during development):

- Python for the tool, VS Code as the editor, Windows 11 on his laptop (RTX 3050, 4 GB graphics memory).
- Supabase's local development setup in Docker for the isolated database copy. It gives the roles and sign-in that the access rules depend on. A plain Postgres container does not.
- PostgreSQL.
- Ollama with a small model (Qwen 2.5, 7 billion parameters) for reading evidence and wording questions. Hosted free-plan models (Groq, Gemini) are possible but hit daily limits in an early test.
- Web framework for the web page: not chosen yet.

His paper PDFs are in D:\Year 3 SEM 1\FYP\Research Papers.

## 7. Safety notes about the tool itself

- The tool runs SQL and files from other people's repos. Treat them as untrusted. Run them only in a disposable container with no access to his real data or network, and throw the copy away after each review.
- An early test (25 Oct) showed a small local model followed instructions planted in code comments in most cases. That is why the model never decides a finding, comments are left out of the evidence it sees, and questions are built from fixed forms where the model only fills in table and column names. How well this works is not yet known.
- A security tool must not leak its own secrets. Set up secret scanning before the first commit. Never commit keys, tokens or real app data.
- Repo visibility: ask Maneet whether the repo stays private for now. The university may own the FYP, so written permission is probably needed before anything is made public. This is an assumption, not a confirmed rule.

## 8. What exists already

- A prototype pipeline from earlier chat sessions. It rebuilt a database in a stand-in Postgres, attacked it as a visitor and two users, and was run on 5 real public apps and 1 app with planted flaws. A zip of it was made on 22 Oct. Its current location is unknown, and the zip may contain only part of the code. Ask Maneet. Treat it as reference, not as the base to build on, unless you both decide otherwise.
- A clickable HTML prototype and a slide deck, both from earlier sessions, in Claude artifacts. They are not code to reuse.

## 9. Evaluation plan (this decides what to build first)

- Planted flaws: apps built in vulnerable and fixed pairs, generated with AI, with a known list of flaws. Build this held-out set before tuning the detector, so the evaluation is not circular.
- Compare recall, precision and false alarms against existing tools. The comparison tools are not final. Candidates are Semgrep, the Supabase linter, and tools in Chapter 2 Table 2 (rlsautotest, rlsgrid, SupaShield, pgrls). The supervisor will help choose which one to replicate.
- Fix test: apply the tool's suggested fix, re-run the attack, and check the app still works.
- Real public apps: labelled case studies only.

## 10. Suggested first session

Do not write code until you and Maneet agree a plan. He wants you to help write the PRD, the roadmap and CLAUDE.md in this repo. Suggested order:

1. Read the Notion pages in section 4 and tell him in plain language what you understood and what is unclear.
2. Ask the questions in section 11.
3. Propose the repo layout and a short CLAUDE.md that points to Notion and does not copy it.
4. Propose a roadmap that starts with the smallest part that can be tested: rebuild one database from migration files, run the visitor and two-user attacks, and print findings. The question step, the GitHub Action and the web page come after.

## 11. Questions to ask him at the start

1. Where is the prototype code or the 22 Oct zip?
2. Which stack goes first, and is Supabase's local setup confirmed?
3. Repo name, and public or private for now?
4. Which web framework for the web page, or leave it until the core works?
5. Has the supervisor chosen which existing tool to replicate or use as the main baseline?
