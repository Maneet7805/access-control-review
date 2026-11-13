# Access review: writes-02-spoofed-owner-vulnerable

We attacked a test copy of your app's database. 1 problem(s) proved, 0 need your decision.

## 1. A signed-in user can add a row to the table "notes" that names someone else as its owner.

**Status:** Proved. We carried out the attack on a test copy of your database and it worked.

**Who can do it:** Any user who is signed in. We tested with a made-up test account, user 11111111-1111-1111-1111-111111111111.

**What we saw:**

- What we did: acted as signed-in user 11111111-1111-1111-1111-111111111111 and tried to add a new row with `INSERT INTO "public"."notes" ("owner_id", "body") VALUES ('x', 'access-review')`.
- What happened: the database accepted the new row. We removed it again, so your data is unchanged.
- The row it accepted (name: value):
  - `body: "x", id: "cccccccc-0000-0000-0000-000000000001", owner_id: "22222222-2222-2222-2222-222222222222"`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Add a row security policy (a rule the database checks before it shows or changes a row) on "notes" so only the right people can add rows.
