# Access review: vulnerable

We attacked a test copy of your app's database. 1 problem(s) proved, 0 need your decision.

## 1. A signed-in user can read rows that belong to other users in the table "profiles".

**Status:** Proved. We carried out the attack on a test copy of your database and it worked.

**Who can do it:** Any user who is signed in. We tested with a made-up test account, user 11111111-1111-1111-1111-111111111111.

**What we saw:**

- What we did: acted as signed-in user 11111111-1111-1111-1111-111111111111 and asked the database for the table's rows with `SELECT * FROM "public"."profiles"`.
- What we got back: 2 rows of data.
- The first 2 rows (each line is one row, shown as name: value):
  - `bio: "bio of A", email: "a@example.test", id: "a8e4b32a-0f54-4ba0-9313-c69b40d3294b", owner_id: "11111111-1111-1111-1111-111111111111"`
  - `bio: "bio of B", email: "b@example.test", id: "3817c839-f283-4e31-a0a6-be7c0a7e212b", owner_id: "22222222-2222-2222-2222-222222222222"`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Add a row security policy (a rule the database checks before it shows or changes a row) on "profiles" so a user can only read rows where "owner_id" equals their own user id (auth.uid()).
