"""Tests for kicad-cli SPICE netlist export (mocked subprocess)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from context.netlist_export import (
    _build_netlist_summary,
    _is_usable_netlist,
    collect_netlist_summary,
)
from utils.config import AppConfig
from utils.kicad_cli import KicadCliNotFoundError

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

PARTIAL_NETLIST = """\
.title KiCad schematic
.model __Q1 NPN
Q1 Net1 Net2 Net3 __Q1
R1 Net1 Net2 10k
.end
"""

EMPTY_SHELL = """\
.title KiCad schematic
.end
"""


class FakeResult:
    def __init__(self, returncode: int = 0, stderr: str = "") -> None:
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = ""


def test_is_usable_netlist() -> None:
    assert _is_usable_netlist(PARTIAL_NETLIST) is True
    assert _is_usable_netlist(EMPTY_SHELL) is False
    assert _is_usable_netlist("") is False


def test_build_netlist_summary_partial_includes_warnings() -> None:
    summary = _build_netlist_summary(
        PARTIAL_NETLIST,
        exit_code=2,
        stderr="Fontconfig warning: ignored\nNo simulation model definition found.\n",
    )
    assert summary["export_status"] == "partial"
    assert summary["kicad_cli_exit_code"] == 2
    assert summary["line_count"] == 5
    assert summary["warnings"] == ["No simulation model definition found."]


def test_collect_netlist_summary_accepts_exit_code_2(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    sch = tmp_path / "demo.kicad_sch"
    sch.write_text("(kicad_sch ...)", encoding="utf-8")

    def fake_runner(cmd, **kwargs):
        out_idx = cmd.index("-o") + 1
        Path(cmd[out_idx]).write_text(PARTIAL_NETLIST, encoding="utf-8")
        return FakeResult(returncode=2, stderr="No simulation model definition found.\n")

    cfg = AppConfig(kicad_cli="/fake/kicad-cli")
    with patch("context.netlist_export.resolve_kicad_cli", return_value=Path("/fake/kicad-cli")):
        summary = collect_netlist_summary(pro, config=cfg, run_subprocess=fake_runner)

    assert summary is not None
    assert summary["export_status"] == "partial"
    assert summary["kicad_cli_exit_code"] == 2
    assert "Q1 Net1 Net2 Net3 __Q1" in summary["text"]
    assert summary["warnings"] == ["No simulation model definition found."]


def test_collect_netlist_summary_ok_on_exit_zero(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    sch = tmp_path / "demo.kicad_sch"
    sch.write_text("(kicad_sch ...)", encoding="utf-8")

    def fake_runner(cmd, **kwargs):
        out_idx = cmd.index("-o") + 1
        Path(cmd[out_idx]).write_text(PARTIAL_NETLIST, encoding="utf-8")
        return FakeResult(returncode=0)

    cfg = AppConfig(kicad_cli="/fake/kicad-cli")
    with patch("context.netlist_export.resolve_kicad_cli", return_value=Path("/fake/kicad-cli")):
        summary = collect_netlist_summary(pro, config=cfg, run_subprocess=fake_runner)

    assert summary is not None
    assert summary["export_status"] == "ok"
    assert summary["kicad_cli_exit_code"] == 0
    assert "warnings" not in summary


def test_collect_netlist_summary_rejects_empty_shell(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    sch = tmp_path / "demo.kicad_sch"
    sch.write_text("(kicad_sch ...)", encoding="utf-8")

    def fake_runner(cmd, **kwargs):
        out_idx = cmd.index("-o") + 1
        Path(cmd[out_idx]).write_text(EMPTY_SHELL, encoding="utf-8")
        return FakeResult(returncode=2, stderr="No simulation model definition found.\n")

    cfg = AppConfig(kicad_cli="/fake/kicad-cli")
    with patch("context.netlist_export.resolve_kicad_cli", return_value=Path("/fake/kicad-cli")):
        summary = collect_netlist_summary(pro, config=cfg, run_subprocess=fake_runner)

    assert summary is None


def test_format_netlist_status_line() -> None:
    from context.netlist_export import format_netlist_status_line

    assert "not exported" in format_netlist_status_line(None)
    assert format_netlist_status_line({"line_count": 10, "export_status": "ok"}) == (
        "SPICE netlist: 10 lines"
    )
    partial = format_netlist_status_line(
        {
            "line_count": 22,
            "export_status": "partial",
            "warnings": ["No simulation model definition found."],
        }
    )
    assert "22 lines" in partial
    assert "partial" in partial
    assert "No simulation model" in partial


def test_collect_netlist_summary_uses_discovered_schematic(tmp_path: Path) -> None:
    """When .kicad_pro stem differs from .kicad_sch name, use discover_schematic_paths."""
    pro = tmp_path / "wrapper.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    sch = tmp_path / "actual_design.kicad_sch"
    sch.write_text("(kicad_sch ...)", encoding="utf-8")

    def fake_runner(cmd, **kwargs):
        assert str(sch) in cmd
        out_idx = cmd.index("-o") + 1
        Path(cmd[out_idx]).write_text(PARTIAL_NETLIST, encoding="utf-8")
        return FakeResult(returncode=2)

    cfg = AppConfig(kicad_cli="/fake/kicad-cli")
    with patch("context.netlist_export.resolve_kicad_cli", return_value=Path("/fake/kicad-cli")):
        summary = collect_netlist_summary(pro, config=cfg, run_subprocess=fake_runner)

    assert summary is not None
    assert summary["line_count"] == 5


def test_collect_netlist_summary_missing_cli(tmp_path: Path) -> None:
    pro = FIXTURES / "testproj.kicad_pro"
    cfg = AppConfig(kicad_cli=None)
    with patch(
        "context.netlist_export.resolve_kicad_cli",
        side_effect=KicadCliNotFoundError("missing"),
    ):
        assert collect_netlist_summary(pro, config=cfg) is None
