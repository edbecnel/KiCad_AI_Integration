"""KiCad Specctra DSN export host adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from routing.errors import RoutingExportError


@dataclass
class DsnExportResult:
    dsn_path: Path
    status: str
    message: str = ""

    @property
    def success(self) -> bool:
        return self.status == "ok"


def _load_pcbnew():
    try:
        import pcbnew  # type: ignore[import-untyped]
    except ImportError as exc:
        return None, str(exc)
    return pcbnew, ""


def export_specctra_dsn(
    pcb_path: Path,
    output_path: Path,
) -> DsnExportResult:
    """
    Export Specctra DSN from a KiCad PCB file.

    Requires pcbnew (embedded KiCad Python). kicad-cli does not support DSN export
    as of KiCad 10.0.4 — see Freerouting_Integration.md Phase 1 findings.
    """
    if not pcb_path.is_file():
        return DsnExportResult(
            dsn_path=output_path,
            status="error",
            message=f"PCB file not found: {pcb_path}",
        )

    pcbnew, import_error = _load_pcbnew()
    if pcbnew is None:
        return DsnExportResult(
            dsn_path=output_path,
            status="unavailable",
            message=(
                "pcbnew is not available for DSN export. "
                "Run from KiCad embedded Python or install KiCad with pcbnew. "
                f"Import error: {import_error}"
            ),
        )

    if not hasattr(pcbnew, "LoadBoard") or not hasattr(pcbnew, "ExportSpecctraDSN"):
        return DsnExportResult(
            dsn_path=output_path,
            status="unavailable",
            message="pcbnew routing APIs (LoadBoard, ExportSpecctraDSN) are not available.",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        board = pcbnew.LoadBoard(str(pcb_path))
        pcbnew.ExportSpecctraDSN(board, str(output_path))
    except Exception as exc:  # noqa: BLE001 — host API boundary
        raise RoutingExportError(f"DSN export failed: {exc}") from exc

    if not output_path.is_file():
        return DsnExportResult(
            dsn_path=output_path,
            status="error",
            message="DSN export completed but output file was not created.",
        )

    return DsnExportResult(dsn_path=output_path, status="ok")
