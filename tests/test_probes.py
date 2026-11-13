from access_review.probes import visitor_reads_rows
from access_review.sandbox import sandbox


def _migration(tmp_path, grant_sql):
    (tmp_path / "001.sql").write_text(
        "CREATE ROLE anon NOLOGIN; CREATE TABLE t (id int); INSERT INTO t VALUES (1);"
        "GRANT USAGE ON SCHEMA public TO anon;" + grant_sql
    )
    return tmp_path


def test_visitor_without_select_privilege_reads_no_rows(tmp_path):
    with sandbox(_migration(tmp_path, "")) as box:
        assert visitor_reads_rows(box, "t").rows_seen == []


def test_table_name_is_quoted_as_an_identifier(tmp_path):
    migration = _migration(tmp_path, 'CREATE TABLE "we""ird" (id int); INSERT INTO "we""ird" VALUES (7);'
                                     'GRANT SELECT ON "we""ird" TO anon;')
    with sandbox(migration) as box:
        assert visitor_reads_rows(box, 'we"ird').rows_seen == [{"id": 7}]


def test_probe_reads_the_table_in_public_even_if_another_schema_has_the_same_name(tmp_path):
    # A schema named after the role comes first on the search path, so a bare table name could be redirected.
    (tmp_path / "001.sql").write_text(
        "create table public.t (id int); insert into public.t values (1), (2); grant select on public.t to anon;"
        "create schema anon; create table anon.t (id int); grant usage on schema anon to anon;"
        "grant select on anon.t to anon;")
    with sandbox(tmp_path, baseline=True) as box:
        assert len(visitor_reads_rows(box, "t").rows_seen) == 2
