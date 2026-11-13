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
