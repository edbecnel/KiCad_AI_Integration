"""Tests for SUBCKT generation and registration."""

from __future__ import annotations

import json
from pathlib import Path

from context.artifacts.store import ArtifactStore
from context.datasheet_resolver import DatasheetResolution
from context.model import ProjectContext
from context.schematic_parse import parse_project_schematics
from context.subckt_generation import (
    build_kicad_hookup_notes,
    generate_subckt_for_part,
    validate_subckt_lib,
)
from providers.types import ProviderResponse, TokenUsage

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

MOCK_LIB = """
* behavioral model
.SUBCKT F0D3180 1 2 3 4 5 6
R1 1 2 1meg
.ENDS
"""


class MockProvider:
    def __init__(self) -> None:
        self.calls = 0

    def send_message(self, prompt: str, *, system: str | None = None, **kwargs) -> ProviderResponse:
        self.calls += 1
        if "Return structured JSON facts only" in prompt:
            payload = {
                "part": "F0D3180",
                "pinout": [{"pin": "1", "name": "A"}],
                "unknowns": [],
                "confidence": "medium",
            }
        else:
            payload = {
                "subckt_name": "F0D3180",
                "lib_text": MOCK_LIB,
                "assumptions": ["behavioral approximation"],
                "abstraction": "behavioral",
            }
        return ProviderResponse(
            text=json.dumps(payload),
            model="mock",
            usage=TokenUsage(input_tokens=10, output_tokens=20),
        )


def test_validate_subckt_lib_accepts_basic_subckt() -> None:
    status, messages = validate_subckt_lib(MOCK_LIB, subckt_name="F0D3180")
    assert status == "syntax-valid"
    assert not messages


def test_generate_subckt_registers_lib(tmp_path: Path) -> None:
    pro = tmp_path / "testproj.kicad_pro"
    pro.touch()
    sch = tmp_path / "testproj.kicad_sch"
    sch.write_text((FIXTURES / "testproj.kicad_sch").read_text(encoding="utf-8"), encoding="utf-8")
    symbols = parse_project_schematics(tmp_path, [sch])
    pdf = tmp_path / "F0D3180.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    lib_path = tmp_path / "artifact_lib"
    store = ArtifactStore(lib_path)
    from context.artifacts.catalog import ComponentRef
    from context.artifacts.store import ProjectContextInfo

    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[sch])
    entry = store.register_datasheet(
        pdf,
        "F0D3180",
        "user_attach",
        project,
        ComponentRef(reference="U3", sheet_path="testproj.kicad_sch"),
    )
    local_pdf = store.resolve_local_path(entry.id)
    ctx = ProjectContext(
        project_path=str(pro),
        project_name="testproj",
        schematics=["testproj.kicad_sch"],
        symbols=symbols,
        datasheet_resolutions={
            "U3": DatasheetResolution(
                status="resolved",
                reference="U3",
                part="F0D3180",
                tier_hint="A",
                artifact_id=entry.id,
                local_path=local_pdf,
            )
        },
    )
    result = generate_subckt_for_part(
        pro,
        ctx,
        "F0D3180",
        provider=MockProvider(),
        store=store,
        tier="B",
    )
    assert result.error is None
    assert result.lib_path is not None
    assert result.lib_path.is_file()
    assert result.artifact_id is not None
    assert result.metadata_dir is not None
    assert (result.metadata_dir / "provenance.json").is_file()
    assert (result.metadata_dir / "validation.json").is_file()
    assert result.hookup is not None
    assert result.hookup.spice_model == "F0D3180"


def test_build_kicad_hookup_notes_includes_spice_fields(tmp_path: Path) -> None:
    lib = tmp_path / "F0D3180.lib"
    lib.write_text(MOCK_LIB, encoding="utf-8")
    notes = build_kicad_hookup_notes(
        part="F0D3180",
        subckt_name="F0D3180",
        lib_path=lib,
        tier_label="context_synthesized",
        validation_status="needs-manual-review",
        assumptions=["draft"],
    )
    assert notes.spice_primitive == "X"
    assert "Spice_Model" in notes.markdown
