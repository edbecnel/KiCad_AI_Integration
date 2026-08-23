"""Transactional board checkpoint for routing workflows."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RoutingCheckpoint:
  """Preserved board state before routing."""

  checkpoint_id: str
  original_pcb_path: Path
  checkpoint_pcb_path: Path
  exports_dir: Path
  created_at: str

  @property
  def candidate_pcb_path(self) -> Path:
    return self.exports_dir / f"{self.checkpoint_id}.candidate.kicad_pcb"


def create_routing_checkpoint(
  pcb_path: Path,
  *,
  exports_dir: Path | None = None,
) -> RoutingCheckpoint:
  """
  Copy the authoritative PCB to a checkpoint before routing.

  The original pcb_path is never modified by routing until explicit accept.
  """
  pcb_path = pcb_path.expanduser().resolve()
  project_root = pcb_path.parent
  base_exports = exports_dir or (project_root / "kicad_ai" / "exports" / "routing")
  base_exports.mkdir(parents=True, exist_ok=True)

  checkpoint_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
  checkpoint_pcb = base_exports / f"{checkpoint_id}.checkpoint.kicad_pcb"
  shutil.copy2(pcb_path, checkpoint_pcb)

  return RoutingCheckpoint(
    checkpoint_id=checkpoint_id,
    original_pcb_path=pcb_path,
    checkpoint_pcb_path=checkpoint_pcb,
    exports_dir=base_exports,
    created_at=checkpoint_id,
  )


def accept_routing_candidate(checkpoint: RoutingCheckpoint) -> Path:
  """Promote routing candidate to authoritative board."""
  candidate = checkpoint.candidate_pcb_path
  if not candidate.is_file():
    raise FileNotFoundError(f"Routing candidate not found: {candidate}")
  shutil.copy2(candidate, checkpoint.original_pcb_path)
  return checkpoint.original_pcb_path


def reject_routing_candidate(checkpoint: RoutingCheckpoint) -> None:
  """Discard routing candidate; authoritative board unchanged."""
  candidate = checkpoint.candidate_pcb_path
  if candidate.is_file():
    candidate.unlink()
