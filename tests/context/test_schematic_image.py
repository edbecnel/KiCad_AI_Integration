"""Tests for schematic image export (mocked subprocess)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from context.schematic_image import export_schematic_image

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class FakeResult:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_export_uses_pdftoppm_at_600_dpi(tmp_path: Path) -> None:
    sch = FIXTURES / "minimal.kicad_sch"
    png_bytes = b"\x89PNG\r\n\x1a\nfake"
    commands_run: list[list[str]] = []

    def fake_runner(cmd, capture_output=True, text=True):
        commands_run.append(list(cmd))
        cmd_str = " ".join(cmd)
        if "export" in cmd_str and "pdf" in cmd_str:
            out_idx = cmd.index("--output") + 1
            prefix = Path(cmd[out_idx])
            pdf_path = prefix.with_suffix(".pdf")
            pdf_path.write_bytes(b"%PDF")
            return FakeResult()
        if "pdftoppm" in cmd_str:
            prefix = Path(cmd[-1])
            prefix.with_suffix(".png").write_bytes(png_bytes)
            return FakeResult()
        if "--help" in cmd:
            return FakeResult(stdout="export pdf svg")
        return FakeResult()

    with patch("context.schematic_image.resolve_kicad_cli", return_value=Path("/fake/kicad-cli")):
        with patch("context.schematic_image._find_pdftoppm", return_value=Path("/fake/pdftoppm")):
            data, meta = export_schematic_image(
                sch,
                dpi=600,
                output_dir=tmp_path,
                run_subprocess=fake_runner,
            )

    assert data == png_bytes
    assert meta.dpi == 600
    ppm_cmds = [c for c in commands_run if "pdftoppm" in c[0]]
    assert ppm_cmds
    assert "600" in ppm_cmds[0]
