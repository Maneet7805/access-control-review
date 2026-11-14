# Access review: functions-02-security-definer-no-check-vulnerable

We attacked a test copy of your app's database. 1 problem(s) proved, 0 need your decision.

## 1. A signed-in user can call the function "set_note_body", which runs with more rights than the caller.

**Status:** Proved. We carried out the attack on a test copy of your database and it worked.

**Who can do it:** Any user who is signed in. We tested with a made-up test account, user 11111111-1111-1111-1111-111111111111.

**What we saw:**

- What we did: acted as signed-in user 11111111-1111-1111-1111-111111111111 and called the function with `SELECT "public"."set_note_body"(gen_random_uuid()::uuid, 'access-review'::text) AS result`, using made-up values.
- What happened: the database ran the function. We undid everything it did, so your data is unchanged.
- What it returned (name: value): `result: ""`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Make "set_note_body" check who is calling and raise an error if the caller may not do this.
