# Access review: decoy-01-public-posts

0 problem(s) proved, 1 need your decision.

## 1. A visitor who is not signed in can read the table "posts", which has no owner column. It may be public on purpose, so the tool cannot tell.

**Status:** Needs your decision. The data was readable, but that may be on purpose.

**Who can do it:** Anyone who visits the app without signing in.

**Proof:**

- What we ran: `SELECT * FROM "posts"`, as a visitor who is not signed in.
- What came back: 1 row(s).
- The first 1 row(s):
  - `{"body": "First post", "id": "bbbbbbbb-0000-0000-0000-000000000001", "title": "Hello"}`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> If "posts" should not be public, turn on row security for it and allow reads only for the people who need them. If it is public on purpose, no change is needed.
