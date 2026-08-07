"""Context inclusion flags for chat and audit prompts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContextIncludeFlags:
    schematic: bool = True
    pcb: bool = True
    bom: bool = True
    erc_drc: bool = True
    netlist: bool = True
