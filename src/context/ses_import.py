"""KiCad Specctra SES import host adapter."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from routing.errors import RoutingImportError


@dataclass
class SesImportResult:
    pcb_path: Path
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


def import_specctra_ses(
    pcb_path: Path,
    ses_path: Path,
    *,
    output_path: Path | None = None,
) -> SesImportResult:
    """
    Import Specctra SES into a KiCad PCB file.

    Writes to output_path when provided (candidate board); otherwise modifies pcb_path.
    Requires pcbnew. kicad-cli does not support SES import as of KiCad 10.0.4.
    """
    pcbnew, import_error = _load_pcbnew()
    if pcbnew is None:
        return SesImportResult(
            pcb_path=output_path or pcb_path,
            status="unavailable",
            message=(
                "pcbnew is not available for SES import. "
                f"Import error: {import_error}"
            ),
        )

    if not hasattr(pcbnew, "LoadBoard") or not hasattr(pcbnew, "ImportSpecctraSES"):
        return SesImportResult(
            pcb_path=output_path or pcb_path,
            status="unavailable",
            message="pcbnew routing APIs (LoadBoard, ImportSpecctraSES) are not available.",
        )

    if not ses_path.is_file():
        return SesImportResult(
            pcb_path=output_path or pcb_path,
            status="error",
            message=f"SES file not found: {ses_path}",
        )

    target = output_path or pcb_path
    if output_path and output_path != pcb_path:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pcb_path, target)

    try:
        board = pcbnew.LoadBoard(str(target))
        pcbnew.ImportSpecctraSES(board, str(ses_path))
        board.Save(str(target))
    except Exception as exc:  # noqa: BLE001 — host API boundary
        raise RoutingImportError(f"SES import failed: {exc}") from exc

    return SesImportResult(pcb_path=target, status="ok")
