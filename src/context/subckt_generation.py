"""AI-assisted SUBCKT / .lib generation and artifact registration."""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from context.artifacts.catalog import ComponentRef
from context.artifacts.store import ArtifactStore, ProjectContextInfo
from context.datasheet_resolver import DatasheetResolution
from context.model import ProjectContext
from context.pdf_text import extract_pdf_text
from context.schematic_parse import SymbolInstance
from prompts.templates.subckt import TIER_LABELS, build_subckt_prompt_for_tier
from providers.base import BaseProvider
from providers.factory import get_provider
from providers.errors import ProviderError
from utils.config import AppConfig, load_config

ValidationStatus = Literal[
    "syntax-valid",
    "syntax-valid-with-warnings",
    "needs-manual-review",
    "failed-validation",
]


@dataclass
class SubcktHookupNotes:
    spice_model: str
    spice_lib: str
    spice_primitive: str
    include_line: str
    pin_order_warning: str = ""
    markdown: str = ""


@dataclass
class SubcktGenerationResult:
    part: str
    tier: str
    tier_label: str
    lib_path: Path | None = None
    artifact_id: str | None = None
    hookup: SubcktHookupNotes | None = None
    validation_status: ValidationStatus = "needs-manual-review"
    validation_messages: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    metadata_dir: Path | None = None
    error: str | None = None


def _parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        return {}
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        if brace:
            text = brace.group(0)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def symbol_context_dict(sym: SymbolInstance) -> dict[str, Any]:
    return {
        "reference": sym.reference,
        "value": sym.value,
        "footprint": sym.footprint,
        "lib_id": sym.lib_id,
        "datasheet": sym.datasheet,
        "spice_model": sym.spice_model,
        "spice_lib": sym.spice_lib,
        "spice_primitive": sym.spice_primitive,
        "custom_fields": sym.custom_fields,
        "sheet_path": sym.sheet_path,
    }


def _default_subckt_name(part: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", part.strip())
    return safe or "PART"


def validate_subckt_lib(
    lib_text: str,
    *,
    subckt_name: str,
    expected_pin_count: int | None = None,
) -> tuple[ValidationStatus, list[str]]:
    messages: list[str] = []
    if not lib_text.strip():
        return "failed-validation", ["Empty .lib text"]

    upper = lib_text.upper()
    if ".SUBCKT" not in upper or ".ENDS" not in upper:
        return "failed-validation", ["Missing .SUBCKT or .ENDS"]

    match = re.search(
        rf"\.SUBCKT\s+{re.escape(subckt_name)}\s+(.+)",
        lib_text,
        re.I,
    )
    if not match:
        messages.append(f".SUBCKT line for {subckt_name} not found")
        status: ValidationStatus = "syntax-valid-with-warnings"
    else:
        pin_tokens = match.group(1).split()
        if expected_pin_count is not None and len(pin_tokens) != expected_pin_count:
            messages.append(
                f"Pin count {len(pin_tokens)} != symbol custom field count {expected_pin_count}"
            )
            status = "syntax-valid-with-warnings"
        else:
            status = "syntax-valid"

    if "placeholder" in lib_text.lower() or "draft" in lib_text.lower():
        messages.append("Model contains draft/placeholder language")
        if status == "syntax-valid":
            status = "needs-manual-review"

    return status, messages


def build_kicad_hookup_notes(
    *,
    part: str,
    subckt_name: str,
    lib_path: Path,
    tier_label: str,
    validation_status: str,
    assumptions: list[str],
) -> SubcktHookupNotes:
    lib_str = str(lib_path)
    include_line = f'.include "{lib_str}"'
    md_lines = [
        f"# KiCad simulation hookup — {part}",
        "",
        f"- **Tier:** {tier_label}",
        f"- **Validation:** {validation_status}",
        f"- **Spice_Primitive:** X",
        f"- **Spice_Model:** `{subckt_name}`",
        f"- **Spice_Lib:** `{lib_str}`",
        f"- **Netlist include:** `{include_line}`",
        "",
        "## Assumptions",
    ]
    md_lines.extend(f"- {a}" for a in assumptions or ["(none listed)"])
    md_lines.extend(
        [
            "",
            "## Manual steps",
            "1. Verify pin order against your KiCad symbol.",
            "2. Run ngspice parse or smoke test on the .lib file.",
            "3. Set symbol Spice fields or use **Apply Spice fields** in the Simulation panel.",
            "4. In KiCad Schematic Editor: save work, then File → Revert to refresh fields after external writes.",
        ]
    )
    return SubcktHookupNotes(
        spice_model=subckt_name,
        spice_lib=lib_str,
        spice_primitive="X",
        include_line=include_line,
        pin_order_warning="Verify .SUBCKT pin order matches KiCad symbol pins.",
        markdown="\n".join(md_lines),
    )


def _write_metadata_bundle(
    project_root: Path,
    part: str,
    *,
    provenance: dict[str, Any],
    validation: dict[str, Any],
    notes: SubcktHookupNotes,
    assumptions: list[str],
) -> Path:
    meta_dir = project_root / "kicad_ai" / "subckt" / part
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2),
        encoding="utf-8",
    )
    (meta_dir / "validation.json").write_text(
        json.dumps(validation, indent=2),
        encoding="utf-8",
    )
    (meta_dir / "kicad-notes.md").write_text(notes.markdown, encoding="utf-8")
    if assumptions:
        (meta_dir / "assumptions.md").write_text(
            "\n".join(f"- {a}" for a in assumptions),
            encoding="utf-8",
        )
    return meta_dir


def _call_provider(
    provider: BaseProvider,
    user: str,
    system: str,
    cfg: AppConfig,
) -> str:
    response = provider.send_message(user, system=system, config=cfg)
    return (response.text or "").strip()


def generate_subckt_for_part(
    project_pro_path: Path,
    ctx: ProjectContext,
    part: str,
    *,
    config: AppConfig | None = None,
    provider: BaseProvider | None = None,
    store: ArtifactStore | None = None,
    tier: Literal["A", "B", "C"] | None = None,
) -> SubcktGenerationResult:
    """
    Generate a draft .lib SUBCKT for one part Value and register it in the shared library.
    """
    cfg = config or load_config()
    pro_path = project_pro_path.expanduser().resolve()
    project_root = pro_path.parent
    part_norm = part.strip()
    matching = [
        sym
        for sym in ctx.symbols
        if (sym.value or sym.reference).strip() == part_norm
    ]
    if not matching:
        return SubcktGenerationResult(
            part=part_norm,
            tier=tier or "C",
            tier_label=TIER_LABELS.get(tier or "C", "inferred_last_resort"),
            error=f"No symbol with Value {part_norm!r}",
        )

    sym = matching[0]
    res = ctx.datasheet_resolutions.get(sym.reference)
    chosen_tier = tier or (res.tier_hint if res else "C")
    tier_label = TIER_LABELS.get(chosen_tier, "inferred_last_resort")
    sym_ctx = symbol_context_dict(sym)

    artifact_store = store or ArtifactStore(cfg.artifact_library_path)
    project_info = ProjectContextInfo(
        project_pro_path=pro_path,
        schematic_paths=[project_root / name for name in ctx.schematics],
    )

    pdf_path: Path | None = None
    datasheet_text = ""
    pdf_error: str | None = None
    if res and res.local_path:
        pdf_path = Path(res.local_path)
        datasheet_text, pdf_error = extract_pdf_text(pdf_path)
    if chosen_tier == "A" and not datasheet_text:
        chosen_tier = "B"
        tier_label = TIER_LABELS["B"]
        if pdf_error:
            pdf_error = pdf_error

    prov: BaseProvider = provider or get_provider(cfg)
    facts: dict[str, Any] = {}
    synthesis_data: dict[str, Any] = {}

    try:
        if chosen_tier == "A":
            user, system = build_subckt_prompt_for_tier(
                "A",
                part_norm,
                sym_ctx,
                datasheet_text=datasheet_text,
                pdf_path=str(pdf_path) if pdf_path else None,
                stage="facts",
            )
            facts = _parse_json_response(_call_provider(prov, user, system, cfg))
            user, system = build_subckt_prompt_for_tier(
                "A",
                part_norm,
                sym_ctx,
                facts=facts,
                stage="synthesis",
            )
            synthesis_data = _parse_json_response(_call_provider(prov, user, system, cfg))
        else:
            project_ctx = {
                "project_name": ctx.project_name,
                "netlist_summary": ctx.netlist_summary,
            }
            user, system = build_subckt_prompt_for_tier(
                chosen_tier,
                part_norm,
                sym_ctx,
                project_context=project_ctx,
            )
            synthesis_data = _parse_json_response(_call_provider(prov, user, system, cfg))
    except ProviderError as exc:
        return SubcktGenerationResult(
            part=part_norm,
            tier=chosen_tier,
            tier_label=tier_label,
            error=str(exc),
        )

    lib_text = str(synthesis_data.get("lib_text") or "").strip()
    subckt_name = str(synthesis_data.get("subckt_name") or _default_subckt_name(part_norm))
    assumptions = synthesis_data.get("assumptions")
    assumption_list = (
        [str(a) for a in assumptions]
        if isinstance(assumptions, list)
        else []
    )

    if not lib_text:
        return SubcktGenerationResult(
            part=part_norm,
            tier=chosen_tier,
            tier_label=tier_label,
            error="AI response did not include lib_text",
        )

    validation_status, validation_messages = validate_subckt_lib(
        lib_text,
        subckt_name=subckt_name,
    )
    if chosen_tier == "C" and validation_status == "syntax-valid":
        validation_status = "needs-manual-review"
        validation_messages.append("Tier C last-resort model requires manual review")

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".lib",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(lib_text)
        tmp_path = Path(tmp.name)

    try:
        entry = artifact_store.register_lib(
            tmp_path,
            part_norm,
            "ai_subckt",
            project_info,
            ComponentRef(
                reference=sym.reference,
                sheet_path=sym.sheet_path,
                sheet_name=sym.sheet_name,
            ),
            tier=tier_label,
        )
        for other in matching[1:]:
            artifact_store.link_existing(
                entry.id,
                project_info,
                ComponentRef(
                    reference=other.reference,
                    sheet_path=other.sheet_path,
                    sheet_name=other.sheet_name,
                ),
                part=part_norm,
            )
    finally:
        tmp_path.unlink(missing_ok=True)

    lib_path = artifact_store.resolve_local_path(entry.id)
    hookup = build_kicad_hookup_notes(
        part=part_norm,
        subckt_name=subckt_name,
        lib_path=lib_path or artifact_store.library_path / entry.file,
        tier_label=tier_label,
        validation_status=validation_status,
        assumptions=assumption_list,
    )

    provenance = {
        "part": part_norm,
        "tier": chosen_tier,
        "tier_label": tier_label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "datasheet_path": str(pdf_path) if pdf_path else None,
        "datasheet_text_error": pdf_error,
        "facts": facts or None,
        "sources_used": (
            ["datasheet_pdf", "kicad_symbol"]
            if chosen_tier == "A"
            else ["kicad_symbol", "project_context"]
            if chosen_tier == "B"
            else ["part_identity"]
        ),
        "artifact_id": entry.id,
    }
    validation_doc = {
        "status": validation_status,
        "messages": validation_messages,
        "subckt_name": subckt_name,
    }
    meta_dir = _write_metadata_bundle(
        project_root,
        part_norm,
        provenance=provenance,
        validation=validation_doc,
        notes=hookup,
        assumptions=assumption_list,
    )

    return SubcktGenerationResult(
        part=part_norm,
        tier=chosen_tier,
        tier_label=tier_label,
        lib_path=lib_path,
        artifact_id=entry.id,
        hookup=hookup,
        validation_status=validation_status,
        validation_messages=validation_messages,
        provenance=provenance,
        assumptions=assumption_list,
        metadata_dir=meta_dir,
    )
