"""Project context model for stretch slice and future MVP expansion."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from context.datasheet_resolver import DatasheetResolution
from context.schematic_image import SchematicImageMeta
from context.schematic_parse import SymbolInstance


@dataclass
class ProjectContext:
    project_path: str
    project_name: str
    schematics: list[str] = field(default_factory=list)
    symbols: list[SymbolInstance] = field(default_factory=list)
    datasheet_resolutions: dict[str, DatasheetResolution] = field(default_factory=dict)
    schematic_image: bytes | None = None
    schematic_image_meta: SchematicImageMeta | None = None
    artifact_manifest_path: str | None = None
    schematic_connectivity: dict[str, Any] | None = None
    pcb_summary: dict[str, Any] | None = None
    netlist_summary: dict[str, Any] | None = None
    schematic_image_error: str | None = None
    ai_discovery_results: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, include_image_bytes: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "project_path": self.project_path,
            "project_name": self.project_name,
            "schematics": self.schematics,
            "symbols": [
                {
                    "reference": s.reference,
                    "value": s.value,
                    "datasheet": s.datasheet,
                    "footprint": s.footprint,
                    "sheet_path": s.sheet_path,
                    "sheet_name": s.sheet_name,
                    "lib_id": s.lib_id,
                }
                for s in self.symbols
            ],
            "datasheet_resolutions": {
                ref: {
                    "status": res.status,
                    "artifact_id": res.artifact_id,
                    "local_path": str(res.local_path) if res.local_path else None,
                    "tier_hint": res.tier_hint,
                    "sources_tried": res.sources_tried,
                    "reference": res.reference,
                    "part": res.part,
                    "url_fetch_outcome": res.url_fetch_outcome,
                    "needs_ai_datasheet_discovery": res.needs_ai_datasheet_discovery,
                }
                for ref, res in self.datasheet_resolutions.items()
            },
            "artifact_manifest_path": self.artifact_manifest_path,
            "schematic_connectivity": self.schematic_connectivity,
            "pcb_summary": self.pcb_summary,
            "netlist_summary": self.netlist_summary,
            "schematic_image_meta": (
                self.schematic_image_meta.to_dict()
                if self.schematic_image_meta
                else None
            ),
        }
        if include_image_bytes and self.schematic_image:
            data["schematic_image_base64"] = base64.b64encode(
                self.schematic_image
            ).decode("ascii")
        elif self.schematic_image is not None:
            data["schematic_image_present"] = True
            data["schematic_image_byte_size"] = len(self.schematic_image)
        return data

    def to_json(self, *, include_image_bytes: bool = False, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(include_image_bytes=include_image_bytes),
            indent=indent,
        )
