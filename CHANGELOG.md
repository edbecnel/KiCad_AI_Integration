# Changelog

[Home](README.md) · [Project Index](PROJECT_INDEX.md)

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- [ADP-013: Routing Abstraction](docs/Architecture/ADP-013-Routing-Abstraction.md) (draft) — engine-neutral routing capability architecture
- [Freerouting Integration](docs/Specifications/Freerouting_Integration.md) specification (draft) — first routing engine reference implementation
- [ADP-013 Phase 1 Review](docs/Architecture/ADP-013-Phase1-Review.md) — investigation findings and gate checklist
- Routing abstraction implementation: `src/routing/`, `src/inference/routing.py`, DSN/SES host adapters, checkpoint workflow
- Routing policy helpers (`src/routing/policy.py`) and AI prompts (`routing_policy.py`, `post_route_review.py`)
- Engineering Engine Provider pattern documented in Platform Architecture (watch item)
- Freerouting config: `freerouting_jar`, `freerouting_cli`, `routing_enabled`, `routing_timeout_sec`

- Incremental context refresh (`context/fingerprint.py`, `context/incremental.py`) and static context cache (`kicad_ai/context_cache.json`)
- Ollama provider (`providers/ollama.py`) and Settings dialog for multi-provider configuration
- Phase 2 exit criteria: provider profile switching and incremental context between chat turns

- ADR-0004: Optional multimodal schematic context (600 DPI default via `kicad-cli` + `pdftoppm`)
- [Prompt Architecture](docs/Architecture/Prompt_Architecture.md): multimodal context and netlist gap-fill prompt sections
- [Netlist Gap Fill](docs/Specifications/Netlist_Gap_Fill.md) specification (Draft)
- Phase 3: three architecture decision records (ADR-0001 through ADR-0003)
- Architecture stubs: Prompt Architecture, AI Provider Interface, Roadmap
- Developer Handbook: `02_AI_Development.md` and `05_Testing.md`

### Changed

- [Netlist Gap Fill](docs/Specifications/Netlist_Gap_Fill.md): shared artifact library with cross-project deduplication and schematic reference tracking
- [Prompt Architecture](docs/Architecture/Prompt_Architecture.md): SUBCKT gap-fill prompt templates (Tier 1–3)
- Context Collection Engine and Project Context Model document optional schematic image output
- [Cost Optimization](docs/AI/Cost_Optimization.md): schematic image token budgeting guidance
- Developer Handbook setup docs: Poppler/`pdftoppm` dependency for 600 DPI export
- `MASTER_TASK_LIST.md`: schematic image export and netlist gap-fill implementation tasks
- `ARCHITECTURE_DECISIONS.md` populated with ADR index
- `PROJECT_INDEX.md` updated with ADRs, architecture stubs, and handbook links
- `MASTER_TASK_LIST.md` documentation items marked complete where applicable

### Added — Phase 4

- Local EDF validation scripts in `scripts/`
- Governance metadata on integration guides

### Changed — Phase 4

- Removed superseded conformance reports
- `ENGINEERING_DOCUMENTATION_FRAMEWORK.md` references local validation scripts

### Added — Phase 2
- Governance documents with normalized metadata (9 files under `docs/Governance/`)
- AI handbook modules with KiCad-specific customization (10 files under `docs/AI/`)
- 14 documentation templates under `docs/Templates/`
- Governance metadata on `PROJECT_CHARTER.md`, `tasks/MASTER_TASK_LIST.md`, and Software Architecture

### Changed

- `PROJECT_INDEX.md` updated with Governance and AI handbook navigation
- `ENGINEERING_DOCUMENTATION_FRAMEWORK.md` adoption status reflects Phase 2 completion

### Added (Phase 1)

- EDF structure-first adoption
- Canonical `docs/` domain layout, root navigation files, and `tasks/` directory
- `PROJECT_INDEX.md`, `PROJECT_CHARTER.md`, `ARCHITECTURE_DECISIONS.md`, `ENGINEERING_DOCUMENTATION_FRAMEWORK.md`
- Migrated documentation from legacy `documentation/` folder to canonical EDF locations

### Changed (Phase 1)

- Repository structure aligned with EDF canonical layout
- `README.md` updated with link to `PROJECT_INDEX.md` and current repository structure
