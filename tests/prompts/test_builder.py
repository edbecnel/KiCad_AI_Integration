"""Tests for prompt builder."""

from __future__ import annotations

import json
from pathlib import Path

from context.collector import collect_stretch_context
from context.model import ProjectContext
from prompts import build_general_review_prompt, build_subckt_prompt, estimate_tokens
from prompts.builder import build_prompt_summary
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
GOLDEN = Path(__file__).resolve().parent / "golden" / "general_review_prompt.txt"


def test_build_general_review_prompt_contains_xml_sections(tmp_path: Path) -> None:
    ds_dir = FIXTURES / "datasheets"
    ds_dir.mkdir(exist_ok=True)
    (ds_dir / "F0D3180.pdf").write_bytes(b"%PDF-1.4 test")

    config = AppConfig(artifact_library_path=tmp_path / "library")
    ctx = collect_stretch_context(
        FIXTURES / "testproj.kicad_pro",
        config=config,
        include_image=False,
    )
    built = build_general_review_prompt(
        ctx,
        "What active parts need review?",
        functional_description="Flyback driver test board",
        include_image=False,
    )
    assert built.template == "general_review"
    assert built.system is not None
    assert "<kicad_python_extracted_data>" in built.text
    assert "<user_question>" in built.text
    assert "<functional_description>" in built.text
    assert "Flyback driver test board" in built.text
    assert "What active parts need review?" in built.text
    assert built.estimated_text_tokens == estimate_tokens(built.text)
    assert "Symbols:" in built.preview_summary


def test_build_prompt_summary_includes_netlist_and_pcb() -> None:
    ctx = ProjectContext(
        project_path="/tmp/demo.kicad_pro",
        project_name="demo",
        netlist_summary={
            "line_count": 22,
            "export_status": "partial",
            "warnings": ["No simulation model definition found."],
        },
        pcb_summary={
            "pcb_file": "demo.kicad_pcb",
            "footprint_count": 5,
            "net_count": 12,
        },
    )
    summary = build_prompt_summary(ctx)
    assert "SPICE netlist: 22 lines (partial" in summary
    assert "PCB (demo.kicad_pcb): 5 footprints, 12 nets" in summary


def test_build_general_review_prompt_golden(tmp_path: Path) -> None:
    ds_dir = FIXTURES / "datasheets"
    ds_dir.mkdir(exist_ok=True)
    (ds_dir / "F0D3180.pdf").write_bytes(b"%PDF-1.4 golden")

    config = AppConfig(artifact_library_path=tmp_path / "library")
    ctx = collect_stretch_context(
        FIXTURES / "testproj.kicad_pro",
        config=config,
        include_image=False,
    )
    built = build_general_review_prompt(
        ctx,
        "Summarize symbols.",
        include_image=False,
    )
    # Stable excerpt for regression detection
    excerpt = built.text[:500]
    if not GOLDEN.is_file():
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(excerpt, encoding="utf-8")

    expected = GOLDEN.read_text(encoding="utf-8")
    assert excerpt.startswith(expected[:80])
    data = json.loads(
        built.text.split("<kicad_python_extracted_data>")[1].split("</kicad_python_extracted_data>")[0].strip()
    )
    assert data["project_name"] == "testproj"
    assert len(data["symbols"]) >= 2


def test_build_subckt_prompt_for_part(tmp_path: Path) -> None:
    ds_dir = FIXTURES / "datasheets"
    ds_dir.mkdir(exist_ok=True)
    (ds_dir / "F0D3180.pdf").write_bytes(b"%PDF-1.4 test")
    config = AppConfig(artifact_library_path=tmp_path / "library")
    ctx = collect_stretch_context(
        FIXTURES / "testproj.kicad_pro",
        config=config,
        include_image=False,
    )
    built = build_subckt_prompt(ctx, "F0D3180", tier="B")
    assert built.template == "subckt_tier_b"
    assert "F0D3180" in built.text
    assert built.system is not None
