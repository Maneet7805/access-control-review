import subprocess

from conftest import PLANTED

from access_review.sandbox import LABEL, sandbox


def _leftover_containers():
    out = subprocess.run(["docker", "ps", "-aq", "--filter", f"label={LABEL}"],
                         capture_output=True, text=True, check=True).stdout
    return out.split()


def _volumes():
    out = subprocess.run(["docker", "volume", "ls", "-q"], capture_output=True, text=True, check=True).stdout
    return set(out.split())


def test_sandbox_leaves_no_docker_volume_behind(tmp_path):
    # Plain postgres:16 declares an anonymous data volume; `docker rm` without -v leaves it behind.
    (tmp_path / "001.sql").write_text("SELECT 1;")
    before = _volumes()
    with sandbox(tmp_path) as box:
        assert box.run("SELECT 1") == "1"
    assert _volumes() == before


def test_sandbox_rebuilds_app_and_leaves_nothing_behind():
    before = _leftover_containers()
    for _ in range(2):
        with sandbox(PLANTED / "rows-01-profiles" / "vulnerable" / "migrations", baseline=True) as box:
            assert box.run("SELECT count(*) FROM profiles") == "2"
        assert _leftover_containers() == before
