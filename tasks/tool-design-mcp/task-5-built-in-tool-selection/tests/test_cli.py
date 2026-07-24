"""Smoke test for cli.py's entry point."""

from cli import main


def test_main_runs_without_error(capsys):
    main()
    out = capsys.readouterr().out
    assert "sent email" in out
    assert "generated report" in out
