# Access review: rows-01-profiles-vulnerable

1 problem(s) proved, 0 need your decision.

## 1. A signed-in user can read rows that belong to other users in the table "profiles".

**Status:** Proved. We ran the attack and saw it work.

**Who can do it:** Any signed-in user (we tested as user 11111111-1111-1111-1111-111111111111).

**Proof:**

- What we ran: `SELECT * FROM "public"."profiles"`, as signed-in user 11111111-1111-1111-1111-111111111111.
- What came back: 2 row(s).
- The first 2 row(s):
  - `{"bio": "bio of A", "email": "a@example.test", "id": "aaaaaaaa-0000-0000-0000-000000000001", "owner_id": "11111111-1111-1111-1111-111111111111"}`
  - `{"bio": "bio of B", "email": "b@example.test", "id": "aaaaaaaa-0000-0000-0000-000000000002", "owner_id": "22222222-2222-2222-2222-222222222222"}`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Add a row security policy (a rule the database checks before it shows or changes a row) on "profiles" so a user can only read rows where "owner_id" equals their own user id (auth.uid()).
