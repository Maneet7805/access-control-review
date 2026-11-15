# Access review: columns-01-self-admin-vulnerable

We attacked a test copy of your app's database. 1 problem(s) proved, 0 need your decision.

## 1. A signed-in user can change the protected column "role" on their own row in the table "members".

**Status:** Proved. We carried out the attack on a test copy of your database and it worked.

**Who can do it:** Any user who is signed in. We tested with a made-up test account, user 11111111-1111-1111-1111-111111111111.

**What we saw:**

- What we did: acted as signed-in user 11111111-1111-1111-1111-111111111111 and tried to change a protected column with `UPDATE "public"."members" SET "role" = 'admin' WHERE "role" IS DISTINCT FROM 'admin'`. Users should not be able to set this value themselves.
- What happened: the database allowed it for 1 row. We undid it, so your data is unchanged.
- The row it changed (name: value):
  - `display_name: "Member A", id: "cccccccc-0000-0000-0000-000000000001", role: "admin", user_id: "11111111-1111-1111-1111-111111111111"`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Stop users from updating "role" on "members": revoke update on that column.
