# Sandbox base image (D1): what each image provides

Status: evidence only. Maneet picks A or B in the pull request. Nothing here decides D1.

Options (roadmap section 6):

- A: `postgres:16` plus our own Supabase stubs.
- B: Supabase's database image, `supabase/postgres:15.19.0.019`.

Evidence comes from `python scripts/probe_images.py`, run on 13 Nov 2026. It starts each image alone, with no published port, and queries the catalogs.

## What each image provides

| Question | `postgres:16` | `supabase/postgres:15.19.0.019` |
| --- | --- | --- |
| Postgres version | 16.15 | 15.19 |
| Roles `anon`, `authenticated`, `service_role`, `authenticator` | none | all four exist |
| `anon`, `authenticated` | - | no login, no bypass of row security |
| `service_role` | - | bypasses row security |
| `authenticator` | - | can log in, does not inherit |
| `postgres` role | superuser | not a superuser, bypasses row security |
| Another superuser | none | `supabase_admin` |
| Schemas `auth`, `storage`, `extensions`, `graphql`, `graphql_public`, `realtime`, `vault` | none | all seven |
| `auth.users` | missing | exists, 21 columns |
| `auth.uid()` | missing | exists, reads setting `request.jwt.claim.sub` |
| `auth.role()` | missing | exists, reads setting `request.jwt.claim.role` |
| `auth.email()` | missing | exists, reads setting `request.jwt.claim.email` |
| `auth.jwt()` | missing | missing |
| Extensions | `plpgsql` | `pg_stat_statements`, `pgcrypto`, `plpgsql`, `supabase_vault`, `uuid-ossp` |
| Default privileges on new tables, sequences, functions in `public` | none | `anon`, `authenticated`, `service_role` get all privileges |
| Image size on Docker Hub | about 640 MB on disk locally | about 330 MB compressed |
| Memory at idle (`docker stats`, two runs) | 31 to 60 MiB | 70 to 71 MiB |

Rerun the script to see the raw tables.

## What this means

- [Certain] Image B already has the roles, their attributes, the `auth` schema, `auth.users` and the default privileges that make Supabase apps rebuild. Option A must recreate all of that by hand.
- [Certain] Image B does not define `auth.jwt()`. In real Supabase the auth service creates it, so any baseline on top of B still needs a stub for it.
- [Certain] In image B, `auth.uid()` reads `request.jwt.claim.sub`, not the JSON setting `request.jwt.claims`. M1.3 must set the setting the function really reads. Setting only `request.jwt.claims` would leave `auth.uid()` returning null in this image.
- [Certain] In image B the `postgres` role is not a superuser, so migrations applied as `postgres` run with the same limits as a hosted project. This helps the known gap that migrations run as superuser today. The superuser is `supabase_admin`.
- [Certain] The current planted apps run `CREATE ROLE anon` and `CREATE ROLE authenticated`. On image B those fail because the roles exist. M1.4 already rewrites the planted apps, so this is expected, not new work.
- [Certain] Image B runs as a single database container. It did not need any of the other Supabase services (login, REST, storage) to give the roles and the `auth` schema.
- [Likely] The extra memory over `postgres:16` is small. Idle memory on `postgres:16` varied between my two runs, so I would not read 10 to 40 MiB as a firm difference.

## Not covered here

- Whether a typical AI-built Supabase migration applies on image B. That is M1.2.
- Postgres 15 against 17. Supabase's local setup defaults to major version 15 (per its configuration page); I did not test 17.
- Whether the table grants shown for `anon` and `authenticated` match a live hosted project. I did not touch any live system.
- What the Supabase docs say about `auth.jwt()` internals. The pages I read describe what it returns, not the setting it reads.

## Recommendation (for Maneet to accept or reject)

Pick B, with a small baseline on top for what B lacks (`auth.jwt()` and the claim settings). The spike found nothing that forces a fall back to A. D1's default in the roadmap is the same: try B, fall back to A.

Risk in B: it pins us to one Supabase image version. Re-run `scripts/probe_images.py` when we change the tag.
