# Access review: views-02-matview-leak-vulnerable

We attacked a test copy of your app's database. 1 problem(s) proved, 0 need your decision.

## 1. The materialized view "all_notes" shows a signed-in user rows of the table "notes" that the table itself hides from that user.

**Status:** Proved. We carried out the attack on a test copy of your database and it worked.

**Who can do it:** Any user who is signed in. We tested with a made-up test account, user 11111111-1111-1111-1111-111111111111.

**What we saw:**

- What we did: acted as signed-in user 11111111-1111-1111-1111-111111111111 and asked the database for the view's rows with `SELECT * FROM "public"."all_notes"`.
- What we got back: 2 rows of data.
- The first 2 rows (each line is one row, shown as name: value):
  - `body: "note of A", id: "cccccccc-0000-0000-0000-000000000001", owner_id: "11111111-1111-1111-1111-111111111111"`
  - `body: "note of B", id: "cccccccc-0000-0000-0000-000000000002", owner_id: "22222222-2222-2222-2222-222222222222"`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Remove access to the materialized view "all_notes" for anon (the database role used for visitors who are not signed in) and authenticated.
