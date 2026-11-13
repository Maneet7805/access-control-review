import json
import socket
import subprocess

import pytest
from conftest import PLANTED

from access_review import sandbox as sandbox_module
from access_review.sandbox import LABEL, START_CAPABILITIES, NotCheckable, sandbox

HOSTILE = PLANTED / "hostile-01-callout"


def _leftover_containers():
    return subprocess.run(["docker", "ps", "-aq", "--filter", f"label={LABEL}"],
                          capture_output=True, text=True, check=True).stdout.split()


def test_migration_cannot_call_out_to_the_network(tmp_path):
    # The listener stands in for "the internet": if the migration reaches it, isolation failed.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.settimeout(1)
        (tmp_path / "001.sql").write_text(
            (HOSTILE / "callout" / "001.sql").read_text().replace("__PORT__", str(listener.getsockname()[1])))
        before = _leftover_containers()
        with pytest.raises(NotCheckable) as caught, sandbox(tmp_path):
            pass
        assert "failed" in caught.value.reason  # the program call itself failed
        with pytest.raises(socket.timeout):
            listener.accept()
    assert _leftover_containers() == before


def test_migration_that_never_finishes_is_stopped(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_module, "MIGRATION_TIMEOUT_SECONDS", 5)
    (tmp_path / "001.sql").write_text((HOSTILE / "loop" / "001.sql").read_text())
    before = _leftover_containers()
    with pytest.raises(NotCheckable) as caught, sandbox(tmp_path):
        pass
    assert (caught.value.kind, caught.value.file) == ("timeout", "001.sql")
    assert _leftover_containers() == before


@pytest.mark.parametrize("baseline", [False, True])
def test_container_runs_with_the_hardened_settings(tmp_path, baseline):
    with sandbox(tmp_path, baseline=baseline) as box:
        config = json.loads(subprocess.run(["docker", "inspect", box.name], capture_output=True, text=True,
                                           check=True).stdout)[0]["HostConfig"]
    assert config["NetworkMode"] == "none"
    assert config["CapDrop"] == ["ALL"]
    assert sorted(config["CapAdd"]) == sorted(f"CAP_{cap}" for cap in START_CAPABILITIES)
    assert "no-new-privileges" in "".join(config["SecurityOpt"])
    assert config["PidsLimit"] > 0
    assert 0 < config["Memory"] == config["MemorySwap"]
    assert config["NanoCpus"] > 0
