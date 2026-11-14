# Access review: writes-05-owner-change-vulnerable

We attacked a test copy of your app's database. 1 problem(s) proved, 0 need your decision.

## 1. A signed-in user can change who owns a row in the table "notes", handing it to another user.

**Status:** Proved. We carried out the attack on a test copy of your database and it worked.

**Who can do it:** Any user who is signed in. We tested with a made-up test account, user 11111111-1111-1111-1111-111111111111.

**What we saw:**

- What we did: acted as signed-in user 11111111-1111-1111-1111-111111111111 and tried to give every row in the table to another user with `UPDATE "public"."notes" SET "owner_id" = '22222222-2222-2222-2222-222222222222'`. Row security should refuse this.
- What happened: the database allowed it for 1 row. We undid it, so your data is unchanged.
- The row it changed, with the new owner (name: value):
  - `body: "note of A", id: "cccccccc-0000-0000-0000-000000000001", owner_id: "22222222-2222-2222-2222-222222222222"`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Add a check to the update policy (a rule the database checks before it shows or changes a row) on "notes" so a changed row must still have "owner_id" equal to the user's own user id (auth.uid()).
