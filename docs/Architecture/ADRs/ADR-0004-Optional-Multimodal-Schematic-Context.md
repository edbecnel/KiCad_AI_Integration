# ADR-0004: Optional Multimodal Schematic Context

[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [Architecture](../README.md) › [ADRs](README.md) › ADR-0004

## Status

Accepted

## Date

2026-07-14

## Decision Owners

- Project maintainers

## Context

Circuit analysis workflows benefit from cross-referencing structured KiCad data (netlists, extracted JSON, ERC/DRC) with the visual schematic layout. Dense schematics with hierarchical sheets, flyback loops, and isolation barriers are difficult to audit from text alone.

KiCad 8 does not expose a reliable in-process Python API to rasterize schematics to PNG the way `pcbnew` can plot a board. The KiCad 8 CLI supports schematic export to SVG, PDF, and DXF — not direct PNG. High-resolution raster images are required for accurate component label OCR and spatial topology reasoning by multimodal LLMs.

Project experience validated that **300 DPI is insufficient** for schematic PNG conversion; **600 DPI** via `pdftoppm` produces acceptable results for AI visual audits.

## Decision

**Phase 1** supports **optional multimodal schematic context** with these constraints:

1. **Export pipeline:** Python subprocess to `kicad-cli sch export pdf`, then rasterize with `pdftoppm` at **600 DPI default**
2. **Not in-process `pcbnew`:** Schematic raster export is orchestrated externally; `pcbnew` remains used for PCB data extraction only
3. **Opt-in only:** UI checkbox "Include schematic image" — off by default or remembers last choice; not sent on every request
4. **User approval required:** Context preview with thumbnail and size estimate; explicit Approve & Send before cloud transmission (per [Security](../../AI/Security.md) and [ADR-0003](ADR-0003-Stateless-Phase-1-Context-Model.md))
5. **Graceful degradation:** If `kicad-cli` or `pdftoppm` is missing or export fails, text-only context still works

### Export commands

```bash
kicad-cli sch export pdf \
  --black-and-white \
  --exclude-drawing-sheet \
  --output /tmp/kicad_ai_export \
  /path/to/project.kicad_sch

pdftoppm -png -r 600 -singlefile \
  /tmp/kicad_ai_export.pdf \
  /tmp/kicad_ai_export
```

Default DPI is **600**. Overridable via config or environment for power users.

## Alternatives Considered

### SVG export + Pillow/cairo rasterization

- Advantages: No Poppler dependency
- Disadvantages: SVG rendering fidelity varies; project experience favors PDF → `pdftoppm` at 600 DPI
- Reason not selected: User-validated `pdftoppm` workflow at 600 DPI

### 300 DPI default

- Advantages: Smaller file size, lower token cost
- Disadvantages: Insufficient resolution for dense schematic label reading
- Reason not selected: Empirical testing showed 300 DPI too low

### Always-on schematic image

- Advantages: Maximum context for every request
- Disadvantages: High token cost; text + netlist often sufficient for connectivity questions
- Reason not selected: Optional checkbox limits cost; images reserved for spatial/topology audits

### Screen capture from Schematic Editor

- Advantages: No external tools
- Disadvantages: Resolution tied to display; not reproducible; requires GUI focus
- Reason not selected: Not automatable or deterministic

### KiCad 9+ native `sch export png --dpi`

- Advantages: Single-step export when available
- Disadvantages: Not available in KiCad 8 (project minimum per ADR-0001)
- Reason not selected as primary: Detect via `kicad-cli sch export --help` and prefer native PNG when available as future fallback

## Consequences

### Positive

- Enables netlist-vs-visual audits and spatial topology analysis
- Deterministic, scriptable export independent of screen resolution
- Black-and-white export improves OCR and label readability
- Aligns with existing reference workflow in [AI Tools for Advanced Circuit Analysis](../../Reference/AI_Tools_for_Advanced_Circuit_Analysis.md)

### Negative

- Requires Poppler (`pdftoppm`) as an external dependency
- Large PNG files increase API token cost
- Unsaved schematic edits are not reflected until user saves project

### Risks

- Multi-sheet hierarchical designs produce multiple pages — mitigate with root-sheet default and optional page selector (Phase 1 stretch)
- `kicad-cli` path varies by platform — mitigate with `KICAD_CLI` env var and discovery logic

## Implementation Notes

- Planned module: `src/context/schematic_image.py` — `export_schematic_image(path, dpi=600, pages=None) -> bytes`
- Extend `ProjectContext` with optional `schematic_image` and `schematic_image_meta` (dpi, sheet, byte size)
- Claude provider attaches `image` content block when present
- See [Prompt Architecture](../Prompt_Architecture.md) for multimodal prompt guidance

## References

- [ADR-0001: KiCad 8 Minimum Version](ADR-0001-KiCad-8-Minimum-Version.md)
- [ADR-0003: Stateless Phase 1 Context Model](ADR-0003-Stateless-Phase-1-Context-Model.md)
- [Prompt Architecture](../Prompt_Architecture.md)
- [Software Architecture](../KiCad_AI_Integration_Software_Architecture.md)
- [Master Task List](../../../tasks/MASTER_TASK_LIST.md) § 1.1, § 1.5

## Parent

- [Architecture Decision Records](README.md)
