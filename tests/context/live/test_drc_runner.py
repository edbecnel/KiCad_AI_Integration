"""Tests for context.live.drc_runner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from context.live.drc_runner import run_live_drc
from utils.config import AppConfig


def test_run_live_drc_no_pcb_file(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    result = run_live_drc(pro, config=AppConfig())
    assert result["drc_live"] is False
    assert "No .kicad_pcb" in result["notes"]


def test_run_live_drc_parses_json_report(tmp_path: Path, monkeypatch) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    pcb = tmp_path / "demo.kicad_pcb"
    pcb.write_text("(kicad_pcb (version 20240108))", encoding="utf-8")

    report_payload = {
        "violations": [
            {"description": "Clearance violation", "severity": "error"},
        ]
    }

    def _fake_run(cmd, **kwargs):
        output = Path(cmd[cmd.index("--output") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report_payload), encoding="utf-8")
        return MagicMock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("context.live.drc_runner.resolve_kicad_cli", lambda _cfg: Path("/usr/bin/kicad-cli"))
    monkeypatch.setattr("context.live.drc_runner.subprocess.run", _fake_run)

    result = run_live_drc(pro, config=AppConfig())
    assert result["drc_live"] is True
    assert result["drc_available"] is True
    assert result["drc_violation_count"] >= 1
    assert any("Clearance" in line for line in result["drc_violation_lines"])


def test_run_live_drc_cli_not_found(tmp_path: Path, monkeypatch) -> None:
    from utils.kicad_cli import KicadCliNotFoundError

    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    (tmp_path / "demo.kicad_pcb").write_text("(kicad_pcb)", encoding="utf-8")

    def _raise(_cfg):
        raise KicadCliNotFoundError("kicad-cli missing")

    monkeypatch.setattr("context.live.drc_runner.resolve_kicad_cli", _raise)
    result = run_live_drc(pro, config=AppConfig())
    assert result["drc_live"] is False
    assert "kicad-cli" in result["notes"]
