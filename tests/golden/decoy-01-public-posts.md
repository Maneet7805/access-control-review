# Access review: decoy-01-public-posts

We attacked a test copy of your app's database. 0 problem(s) proved, 1 need your decision.

## 1. A visitor who is not signed in can read the table "posts", which has no owner column. It may be public on purpose, so the tool cannot tell.

**Status:** Needs your decision. Anyone could read this data. That may be on purpose, so only you can say.

**Who can do it:** Anyone who opens your app without signing in.

**What we saw:**

- What we did: acted as a visitor who is not signed in and asked the database for the table's rows with `SELECT * FROM "public"."posts"`.
- What we got back: 1 row of data.
- The row (each line is one row, shown as name: value):
  - `body: "First post", id: "bbbbbbbb-0000-0000-0000-000000000001", title: "Hello"`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> If "posts" should not be public, turn on row security for it and allow reads only for the people who need them. If it is public on purpose, no change is needed.
