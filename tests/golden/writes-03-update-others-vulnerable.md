# Access review: writes-03-update-others-vulnerable

We attacked a test copy of your app's database. 1 problem(s) proved, 0 need your decision.

## 1. A signed-in user can change rows that belong to other users in the table "notes".

**Status:** Proved. We carried out the attack on a test copy of your database and it worked.

**Who can do it:** Any user who is signed in. We tested with a made-up test account, user 11111111-1111-1111-1111-111111111111.

**What we saw:**

- What we did: acted as signed-in user 11111111-1111-1111-1111-111111111111 and tried to change every row in the table with `UPDATE "public"."notes" SET "body" = 'access-review'`. Row security should limit this to the user's own rows.
- What happened: the database allowed it for 2 rows, including rows that belong to other users. We undid it, so your data is unchanged.
- The rows it changed (name: value):
  - `body: "note of A", id: "cccccccc-0000-0000-0000-000000000001", owner_id: "11111111-1111-1111-1111-111111111111"`
  - `body: "note of B", id: "cccccccc-0000-0000-0000-000000000002", owner_id: "22222222-2222-2222-2222-222222222222"`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Add a row security policy (a rule the database checks before it shows or changes a row) on "notes" so a user can only change their own rows.
