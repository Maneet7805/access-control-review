# Access review: columns-03-phone-exposed-vulnerable

We attacked a test copy of your app's database. 1 problem(s) proved, 0 need your decision.

## 1. A visitor who is not signed in can read the private column "phone" of other people in the table "directory".

**Status:** Proved. We carried out the attack on a test copy of your database and it worked.

**Who can do it:** Anyone who opens your app without signing in.

**What we saw:**

- What we did: acted as a visitor who is not signed in and asked the database for a private column with `SELECT "phone" FROM "public"."directory"`. Only the people it belongs to should be able to read it.
- What we got back: 2 rows of data. Nothing was changed.
- The first 2 rows (name: value):
  - `phone: "+60 12-000 0001"`
  - `phone: "+60 12-000 0002"`

**Suggested fix** (you can give this text to your own AI assistant; this tool never changes your code):

> Stop visitors and signed-in users from reading "phone" on "directory": take away their read access to the table, then give read access only on the columns that are public.
