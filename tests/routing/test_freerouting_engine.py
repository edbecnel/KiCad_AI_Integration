"""Tests for FreeroutingRoutingEngine."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from routing.freerouting import FreeroutingRoutingEngine
from routing.types import BoardReference, RoutingRequest


@pytest.fixture
def sample_pcb(tmp_path: Path) -> Path:
    pcb = tmp_path / "board.kicad_pcb"
    pcb.write_text('(kicad_pcb (version 20240108) (generator "test"))\n', encoding="utf-8")
    return pcb


def test_capabilities_not_installed() -> None:
    engine = FreeroutingRoutingEngine(jar="/nonexistent/freerouting.jar")
    caps = engine.capabilities()
    assert caps.engine_id == "freerouting"
    assert caps.installed is False


def test_route_missing_pcb(tmp_path: Path) -> None:
    jar = tmp_path / "freerouting.jar"
    jar.write_text("jar", encoding="utf-8")
    engine = FreeroutingRoutingEngine(jar=str(jar))
    request = RoutingRequest(
        board_reference=BoardReference(
            project_path=tmp_path / "board.kicad_pro",
            pcb_path=tmp_path / "missing.kicad_pcb",
        )
    )
    result = engine.route(request)
    assert result.success is False
    assert any("not found" in e.lower() for e in result.errors)


def test_route_dsn_unavailable_without_pcbnew(sample_pcb: Path, tmp_path: Path) -> None:
    jar = tmp_path / "freerouting.jar"
    jar.write_text("jar", encoding="utf-8")
    engine = FreeroutingRoutingEngine(jar=str(jar))
    request = RoutingRequest(
        board_reference=BoardReference(
            project_path=sample_pcb.with_suffix(".kicad_pro"),
            pcb_path=sample_pcb,
        )
    )
    result = engine.route(request)
    assert result.success is False
    assert any("pcbnew" in e.lower() or "dsn" in e.lower() for e in result.errors)


def test_route_success_mocked_subprocess(sample_pcb: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jar = tmp_path / "freerouting.jar"
    jar.write_text("jar", encoding="utf-8")

    def fake_export(pcb_path: Path, output_path: Path):
        from context.dsn_export import DsnExportResult

        output_path.write_text("(dsn mock)\n", encoding="utf-8")
        return DsnExportResult(dsn_path=output_path, status="ok")

    def fake_import(pcb_path: Path, ses_path: Path, *, output_path: Path | None = None):
        from context.ses_import import SesImportResult

        target = output_path or pcb_path
        target.write_text("(kicad_pcb routed)\n", encoding="utf-8")
        return SesImportResult(pcb_path=target, status="ok")

    def fake_run(cmd, **kwargs):
        ses_path = Path(cmd[cmd.index("-do") + 1])
        ses_path.write_text("(ses mock)\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr("routing.freerouting.export_specctra_dsn", fake_export)
    monkeypatch.setattr("routing.freerouting.import_specctra_ses", fake_import)

    engine = FreeroutingRoutingEngine(jar=str(jar), run_subprocess=fake_run)
    request = RoutingRequest(
        board_reference=BoardReference(
            project_path=sample_pcb.with_suffix(".kicad_pro"),
            pcb_path=sample_pcb,
        )
    )
    result = engine.route(request)
    assert result.success is True
    assert result.candidate_pcb_path is not None
    assert result.candidate_pcb_path.is_file()
    assert result.original_pcb_path == sample_pcb.resolve()
