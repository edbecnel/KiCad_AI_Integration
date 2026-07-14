"""Tests for prompt builder."""

from __future__ import annotations

import json
from pathlib import Path

from context.collector import collect_stretch_context
from prompts import build_general_review_prompt, estimate_tokens
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
