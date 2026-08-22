"""Tests for Freerouting CLI resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from routing.errors import RoutingToolNotFoundError
from utils.freerouting_cli import FreeroutingResolution, resolve_freerouting, try_resolve_freerouting


def test_freerouting_resolution_builds_jar_command(tmp_path: Path) -> None:
    jar = tmp_path / "freerouting.jar"
    jar.write_text("jar", encoding="utf-8")
    resolution = FreeroutingResolution(jar_path=jar)
    dsn = tmp_path / "board.dsn"
    ses = tmp_path / "board.ses"
    cmd = resolution.build_command(dsn_path=dsn, ses_path=ses, excluded_net_classes=["GND"])
    assert cmd[0].endswith("java")
    assert "-jar" in cmd
    assert str(jar) in cmd
    assert "-inc" in cmd
    assert "GND" in cmd


def test_freerouting_resolution_builds_cli_command(tmp_path: Path) -> None:
    cli = tmp_path / "freerouting"
    cli.write_text("#!/bin/sh\n", encoding="utf-8")
    cli.chmod(0o755)
    resolution = FreeroutingResolution(cli_path=cli)
    cmd = resolution.build_command(
        dsn_path=tmp_path / "a.dsn",
        ses_path=tmp_path / "a.ses",
    )
    assert cmd[0] == str(cli)
    assert "-de" in cmd


def test_resolve_freerouting_explicit_jar(tmp_path: Path) -> None:
    jar = tmp_path / "freerouting.jar"
    jar.write_text("jar", encoding="utf-8")
    resolution = resolve_freerouting(jar=str(jar))
    assert resolution.jar_path == jar.resolve()


def test_resolve_freerouting_not_found() -> None:
    with pytest.raises(RoutingToolNotFoundError):
        resolve_freerouting(jar="/nonexistent/freerouting.jar")


def test_try_resolve_freerouting_returns_none_when_missing() -> None:
    assert try_resolve_freerouting(jar="/nonexistent/freerouting.jar") is None
