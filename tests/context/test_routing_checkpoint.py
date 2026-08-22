"""Tests for routing checkpoint workflow."""

from __future__ import annotations

from pathlib import Path

from context.routing_checkpoint import (
    accept_routing_candidate,
    create_routing_checkpoint,
    reject_routing_candidate,
)


def test_checkpoint_preserves_original(tmp_path: Path) -> None:
    pcb = tmp_path / "board.kicad_pcb"
    pcb.write_text("(kicad_pcb original)\n", encoding="utf-8")
    original_text = pcb.read_text(encoding="utf-8")

    checkpoint = create_routing_checkpoint(pcb)
    assert checkpoint.checkpoint_pcb_path.is_file()
    assert checkpoint.original_pcb_path == pcb.resolve()

    candidate = checkpoint.candidate_pcb_path
    candidate.write_text("(kicad_pcb routed)\n", encoding="utf-8")

    accept_routing_candidate(checkpoint)
    assert pcb.read_text(encoding="utf-8") == "(kicad_pcb routed)\n"
    pcb.write_text(original_text, encoding="utf-8")


def test_reject_discards_candidate(tmp_path: Path) -> None:
    pcb = tmp_path / "board.kicad_pcb"
    pcb.write_text("(kicad_pcb original)\n", encoding="utf-8")
    checkpoint = create_routing_checkpoint(pcb)
    candidate = checkpoint.candidate_pcb_path
    candidate.write_text("(kicad_pcb routed)\n", encoding="utf-8")

    reject_routing_candidate(checkpoint)
    assert not candidate.is_file()
    assert pcb.read_text(encoding="utf-8") == "(kicad_pcb original)\n"
