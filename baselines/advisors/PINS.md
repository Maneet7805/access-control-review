# Supabase advisors pins

- File: `splinter.sql`, from `supabase/splinter` at commit `cc529aa9d3eeffd2e64576c7591e60b22abd205c`, the single-query file built from `lints/`. Licence: PostgreSQL License (the repository's LICENSE).
- SHA-256 of the file: `e652eb2be316eaf44ad523e8b0e6e76bb4952942be86692811064d0b72402b46`.
- Run by `run_splinter.py` through `docker exec psql` in the sandbox database. No setting is changed, so the API-exposure lints cover the `public` schema only.
- These are read-only catalog queries. They are checks, not attacks.
