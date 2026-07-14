"""Schematic image export per ADR-0004 (600 DPI via kicad-cli + pdftoppm)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from utils.kicad_cli import KicadCliNotFoundError, resolve_kicad_cli


class PdftoppmNotFoundError(FileNotFoundError):
    """Raised when pdftoppm is not on PATH."""


class SchematicExportError(RuntimeError):
    """Raised when schematic export fails."""


@dataclass
class SchematicImageMeta:
    dpi: int
    byte_size: int
    source_command: str
    schematic_path: str
    cached_path: str | None = None
    page: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "dpi": self.dpi,
            "byte_size": self.byte_size,
            "source_command": self.source_command,
            "schematic_path": self.schematic_path,
            "cached_path": self.cached_path,
            "page": self.page,
        }


def _find_pdftoppm() -> Path:
    found = shutil.which("pdftoppm")
    if not found:
        raise PdftoppmNotFoundError(
            "pdftoppm not found. Install Poppler (e.g. brew install poppler)."
        )
    return Path(found)


def _kicad_cli_supports_native_png(kicad_cli: Path) -> bool:
    try:
        result = subprocess.run(
            [str(kicad_cli), "sch", "export", "--help"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        help_text = (result.stdout or "") + (result.stderr or "")
        return "png" in help_text.lower() and "dpi" in help_text.lower()
    except (subprocess.SubprocessError, OSError):
        return False


def export_schematic_image(
    schematic_path: Path,
    *,
    dpi: int = 600,
    pages: list[int] | None = None,
    output_dir: Path | None = None,
    kicad_cli: str | Path | None = None,
    run_subprocess: Callable[..., subprocess.CompletedProcess] | None = None,
) -> tuple[bytes, SchematicImageMeta]:
    """
    Export schematic to PNG bytes.

    Default pipeline: kicad-cli PDF export → pdftoppm at 600 DPI.
    Uses native PNG export when KiCad 9+ supports it.
    """
    schematic_path = schematic_path.expanduser().resolve()
    if not schematic_path.is_file():
        raise SchematicExportError(f"Schematic not found: {schematic_path}")

    cli = resolve_kicad_cli(str(kicad_cli) if kicad_cli else None)
    runner = run_subprocess or subprocess.run
    source_command = ""

    with tempfile.TemporaryDirectory(prefix="kicad_ai_sch_") as tmp:
        tmp_path = Path(tmp)
        png_path: Path

        if _kicad_cli_supports_native_png(cli):
            png_path = tmp_path / f"{schematic_path.stem}.png"
            cmd = [
                str(cli),
                "sch",
                "export",
                "png",
                "--dpi",
                str(dpi),
                "--output",
                str(png_path),
                str(schematic_path),
            ]
            source_command = " ".join(cmd)
            result = runner(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise SchematicExportError(
                    f"kicad-cli png export failed: {result.stderr or result.stdout}"
                )
            if not png_path.is_file():
                raise SchematicExportError("kicad-cli did not produce PNG output")
        else:
            pdf_path = tmp_path / f"{schematic_path.stem}.pdf"
            pdf_cmd = [
                str(cli),
                "sch",
                "export",
                "pdf",
                "--black-and-white",
                "--exclude-drawing-sheet",
                "--output",
                str(pdf_path.with_suffix("")),
                str(schematic_path),
            ]
            source_command = " ".join(pdf_cmd)
            result = runner(pdf_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise SchematicExportError(
                    f"kicad-cli pdf export failed: {result.stderr or result.stdout}"
                )
            if not pdf_path.is_file():
                alt = tmp_path / f"{schematic_path.stem}"
                if alt.with_suffix(".pdf").is_file():
                    pdf_path = alt.with_suffix(".pdf")
                elif list(tmp_path.glob("*.pdf")):
                    pdf_path = next(tmp_path.glob("*.pdf"))
                else:
                    raise SchematicExportError("kicad-cli did not produce PDF output")

            pdftoppm = _find_pdftoppm()
            prefix = tmp_path / schematic_path.stem
            ppm_cmd = [
                str(pdftoppm),
                "-png",
                "-r",
                str(dpi),
                "-singlefile",
                str(pdf_path),
                str(prefix),
            ]
            source_command = f"{source_command}; {' '.join(ppm_cmd)}"
            ppm_result = runner(ppm_cmd, capture_output=True, text=True)
            if ppm_result.returncode != 0:
                raise SchematicExportError(
                    f"pdftoppm failed: {ppm_result.stderr or ppm_result.stdout}"
                )
            png_path = prefix.with_suffix(".png")
            if not png_path.is_file():
                candidates = list(tmp_path.glob("*.png"))
                if not candidates:
                    raise SchematicExportError("pdftoppm did not produce PNG output")
                png_path = candidates[0]

        png_bytes = png_path.read_bytes()
        cached: Path | None = None
        if output_dir is not None:
            output_dir = output_dir.expanduser()
            output_dir.mkdir(parents=True, exist_ok=True)
            cached = output_dir / f"{schematic_path.stem}_{dpi}.png"
            cached.write_bytes(png_bytes)

        meta = SchematicImageMeta(
            dpi=dpi,
            byte_size=len(png_bytes),
            source_command=source_command,
            schematic_path=str(schematic_path),
            cached_path=str(cached) if cached else None,
            page=pages[0] if pages else None,
        )
        return png_bytes, meta


# Re-export discovery errors for callers
__all__ = [
    "KicadCliNotFoundError",
    "PdftoppmNotFoundError",
    "SchematicExportError",
    "SchematicImageMeta",
    "export_schematic_image",
]
