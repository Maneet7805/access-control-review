from conftest import PLANTED, ROOT

from access_review.demo_sandbox import main

BROKEN = ROOT / "tests" / "fixtures" / "broken"


def _rows_by_person(capsys, folder):
    assert main([str(folder)]) == 0
    lines = capsys.readouterr().out.splitlines()[1:]
    return {" ".join(line.split()[:-1]): int(line.split()[-1]) for line in lines}


def test_vulnerable_app_shows_every_row_to_everyone(capsys):
    counts = _rows_by_person(capsys, PLANTED / "rows-01-profiles" / "vulnerable" / "migrations")
    assert counts == {"visitor": 2, "user A": 2, "user B": 2}


def test_fixed_twin_shows_visitor_nothing_and_users_their_own(capsys):
    # Negative control: the same command on the fixed twin gives different numbers.
    counts = _rows_by_person(capsys, PLANTED / "rows-01-profiles" / "fixed" / "migrations")
    assert counts == {"visitor": 0, "user A": 1, "user B": 1}


def test_broken_app_says_why_it_is_not_checkable(capsys):
    assert main([str(BROKEN / "syntax_error")]) == 1
    assert "001.sql, line 3" in capsys.readouterr().out


def test_no_folder_prints_usage(capsys):
    assert main([]) == 2
    assert "Usage" in capsys.readouterr().out
