# Access review: writes-01-visitor-insert-vulnerable

We attacked a test copy of your app's database. 1 problem(s) proved, 0 need your decision.

## 1. A visitor who is not signed in can add rows to the table "notes".

**Status:** Proved. We carried out the attack on a test copy of your database and it worked.

**Who can do it:** Anyone who opens your app without signing in.

**What we saw:**

- What we did: acted as a visitor who is not signed in and tried to add a new row with `INSERT INTO "public"."notes" ("owner_id", "body") VALUES ('x', 'access-review')`.
- What happened: the database accepted the new row. We removed it again, so your data is unchanged.
- The row it accepted (name: value):
  - `body: "x", id: "cccccccc-0000-0000-0000-000000000001", owner_id: "11111111-1111-1111-1111-111111111111"`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Add a row security policy (a rule the database checks before it shows or changes a row) on "notes" so only the right people can add rows.
