"""Write resolved datasheet URLs back to .kicad_sch symbol properties."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from context.artifacts.store import ArtifactStore
from context.datasheet_requirements import classify_datasheet_requirement
from context.datasheet_resolver import normalize_datasheet_url
from context.model import ProjectContext
from context.schematic_parse import SymbolInstance, _extract_symbol_blocks, _read_properties
from context.builtin_sim_models import BuiltinSimHookup, resolve_builtin_simulation_hookup
from context.schematic_sim_write import (
    build_sim_pins_mapping,
    kicad9_sim_hookup_incomplete,
    load_subckt_metadata,
    parse_lib_symbol_pin_names,
)
from typing import Literal

FieldIssueKind = Literal["ok", "empty", "local_path", "stale_url", "mismatch"]

FIELD_ISSUE_LABELS: dict[FieldIssueKind, str] = {
    "ok": "OK",
    "empty": "Empty field",
    "local_path": "Local path (not HTTPS)",
    "stale_url": "URL failed to fetch",
    "mismatch": "URL differs from resolved",
}

_FIELD_ISSUE_RANK: dict[FieldIssueKind, int] = {
    "ok": 0,
    "local_path": 1,
    "mismatch": 2,
    "stale_url": 3,
    "empty": 4,
}


@dataclass
class DatasheetFieldUpdate:
    """One symbol Datasheet property written to a schematic file."""

    sheet_path: str
    reference: str
    part: str
    old_value: str
    new_url: str


@dataclass
class DatasheetFieldWriteResult:
    updated: list[DatasheetFieldUpdate]
    skipped: list[str]

    @property
    def changed_count(self) -> int:
        return len(self.updated)


def _escape_sch_property_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _datasheet_property_pattern() -> re.Pattern[str]:
    return re.compile(
        r'\(property\s+"Datasheet"\s+"((?:[^"\\]|\\.)*)"(?:\s*\(at[^)]*\))*\s*\)',
        re.DOTALL,
    )


def _replace_datasheet_in_block(block: str, url: str) -> tuple[str, bool]:
    escaped = _escape_sch_property_value(url)
    prop_re = _datasheet_property_pattern()
    match = prop_re.search(block)
    if match:
        at_match = re.search(
            r'\(property\s+"Datasheet"\s+"[^"]*"\s*(\(at[^)]*\))',
            block,
            re.DOTALL,
        )
        at_clause = at_match.group(1) if at_match else "(at 0 0 0)"
        new_prop = f'(property "Datasheet" "{escaped}"\n      {at_clause}\n    )'
        new_block = prop_re.sub(new_prop, block, count=1)
        return new_block, new_block != block

    value_match = re.search(
        r'(\(property\s+"Value"\s+"[^"]*"(?:\s*\(at[^)]*\))?\s*\))',
        block,
        re.DOTALL,
    )
    insert = f'\n    (property "Datasheet" "{escaped}"\n      (at 0 0 0)\n    )'
    if value_match:
        pos = value_match.end()
        new_block = block[:pos] + insert + block[pos:]
        return new_block, True
    closing = block.rfind(")")
    if closing == -1:
        return block, False
    new_block = block[:closing] + insert + block[closing:]
    return new_block, True


def _update_datasheet_in_content(content: str, reference: str, url: str) -> tuple[str, bool]:
    ref_norm = reference.strip()
    changed = False
    parts: list[str] = []
    last = 0
    for block in _extract_symbol_blocks(content):
        start = content.find(block, last)
        if start == -1:
            continue
        end = start + len(block)
        props = _read_properties(block)
        if props.get("Reference", "").strip() != ref_norm:
            parts.append(content[last:end])
            last = end
            continue
        new_block, block_changed = _replace_datasheet_in_block(block, url)
        parts.append(content[last:start])
        parts.append(new_block)
        last = end
        changed = changed or block_changed
    parts.append(content[last:])
    if not changed:
        return content, False
    return "".join(parts), True


def update_symbol_datasheet_property(
    schematic_path: Path,
    reference: str,
    datasheet_url: str,
) -> bool:
    """Update the Datasheet property for one placed symbol in a .kicad_sch file."""
    path = schematic_path.expanduser().resolve()
    content = path.read_text(encoding="utf-8")
    new_content, changed = _update_datasheet_in_content(
        content,
        reference,
        datasheet_url,
    )
    if changed:
        path.write_text(new_content, encoding="utf-8")
    return changed


def resolved_https_url_for_symbol(
    sym: SymbolInstance,
    resolution: object | None,
    store: ArtifactStore,
    ai_discovery_results: dict[str, object] | None,
) -> str | None:
    """Return the HTTPS URL to write for a resolved symbol, if known."""
    if resolution is None or getattr(resolution, "status", None) != "resolved":
        return None

    artifact_id = getattr(resolution, "artifact_id", None)
    if artifact_id:
        entry = store.catalog.get_by_id(str(artifact_id))
        if entry is not None and entry.source_url and entry.source_url.startswith("https://"):
            return entry.source_url
        for log_entry in store.url_fetch_log.entries:
            if (
                log_entry.artifact_id == artifact_id
                and log_entry.source_url.startswith("https://")
                and log_entry.status == "downloaded"
            ):
                return log_entry.source_url

    part = (sym.value or sym.reference).strip()
    discovery = (ai_discovery_results or {}).get(part)
    if discovery is not None:
        selected = getattr(discovery, "selected_url", None)
        if selected and str(selected).startswith("https://"):
            return str(selected)

    if sym.datasheet.startswith("https://"):
        return sym.datasheet

    return None


def symbol_datasheet_field_issue(
    sym: SymbolInstance,
    resolution: object | None,
    store: ArtifactStore,
    ai_discovery_results: dict[str, object] | None,
) -> tuple[FieldIssueKind, str]:
    """Classify whether a symbol's Datasheet property needs cleanup."""
    field = sym.datasheet.strip()
    res_status = getattr(resolution, "status", None) if resolution else None
    resolved_url = resolved_https_url_for_symbol(
        sym, resolution, store, ai_discovery_results
    )

    if not field:
        if res_status in ("missing", "fetch_failed", None):
            return "empty", "Datasheet property is empty"
        if resolved_url:
            return "empty", "Empty field; resolved HTTPS URL available"
        return "empty", "Datasheet property is empty"

    if field.startswith("https://"):
        norm_field = normalize_datasheet_url(field)
        if res_status in ("missing", "fetch_failed"):
            return "stale_url", "Symbol HTTPS URL did not resolve to a PDF"
        if resolved_url:
            norm_resolved = normalize_datasheet_url(resolved_url)
            if norm_field != norm_resolved:
                return "mismatch", "Symbol URL differs from resolved catalog URL"
        return "ok", ""

    if resolved_url:
        return "local_path", "Non-HTTPS field; resolved URL can be written to schematic"
    if res_status == "resolved":
        return "local_path", "Non-HTTPS field; PDF resolved in shared library"
    return "local_path", "Datasheet is not an HTTPS URL"


def summarize_symbol_field_issues(
    symbols: list[SymbolInstance],
    resolutions: dict[str, object],
    store: ArtifactStore,
    ai_discovery_results: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    """Group required parts whose symbol Datasheet field is empty or incorrect."""
    grouped: dict[str, dict[str, object]] = {}

    for sym in symbols:
        if classify_datasheet_requirement(sym) != "required":
            continue
        part = (sym.value or sym.reference).strip()
        res = resolutions.get(sym.reference)
        kind, detail = symbol_datasheet_field_issue(
            sym,
            res,
            store,
            ai_discovery_results,
        )
        bucket = grouped.setdefault(
            part,
            {
                "part": part,
                "references": [],
                "symbol_fields": set(),
                "field_issue": "ok",
                "field_issue_detail": "",
                "resolved_url": None,
                "status": str(getattr(res, "status", "missing") if res else "missing"),
                "is_resolved": bool(res is not None and getattr(res, "status", None) == "resolved"),
            },
        )
        refs = bucket["references"]
        assert isinstance(refs, list)
        refs.append(sym.reference)
        fields = bucket["symbol_fields"]
        assert isinstance(fields, set)
        fields.add(sym.datasheet.strip() or "(empty)")
        current = str(bucket["field_issue"])
        if _FIELD_ISSUE_RANK[kind] > _FIELD_ISSUE_RANK[current]:  # type: ignore[index]
            bucket["field_issue"] = kind
            bucket["field_issue_detail"] = detail
        resolved = resolved_https_url_for_symbol(
            sym, res, store, ai_discovery_results
        )
        if resolved and bucket["resolved_url"] is None:
            bucket["resolved_url"] = resolved

    out: list[dict[str, object]] = []
    for part in sorted(grouped):
        entry = grouped[part]
        fields = entry["symbol_fields"]
        assert isinstance(fields, set)
        if len(fields) > 1:
            entry["field_issue"] = "mismatch"
            entry["field_issue_detail"] = "References disagree on Datasheet field value"
        if entry["field_issue"] == "ok":
            continue
        entry["symbol_fields"] = sorted(fields)
        refs = entry["references"]
        assert isinstance(refs, list)
        entry["reference_count"] = len(refs)
        out.append(entry)
    return out


def write_resolved_datasheet_urls(
    project_pro_path: Path,
    ctx: ProjectContext,
    store: ArtifactStore,
    *,
    part: str | None = None,
    only_if_empty: bool = False,
) -> DatasheetFieldWriteResult:
    """
    Write resolved HTTPS datasheet URLs to symbol Datasheet fields in .kicad_sch.

    Updates only symbols that resolved successfully and have a known HTTPS URL
    (catalog ``source_url``, AI discovery selection, or existing symbol URL).
    """
    pro_path = project_pro_path.expanduser().resolve()
    project_root = pro_path.parent
    artifact_store = store
    part_norm = part.strip() if part else None

    updated: list[DatasheetFieldUpdate] = []
    skipped: list[str] = []
    file_cache: dict[Path, str] = {}
    dirty_files: set[Path] = set()

    for sym in ctx.symbols:
        sym_part = (sym.value or sym.reference).strip()
        if part_norm is not None and sym_part != part_norm:
            continue

        res = ctx.datasheet_resolutions.get(sym.reference)
        url = resolved_https_url_for_symbol(
            sym,
            res,
            artifact_store,
            ctx.ai_discovery_results,
        )
        if url is None:
            skipped.append(f"{sym.reference}: no HTTPS URL to write")
            continue
        if only_if_empty and sym.datasheet.strip():
            skipped.append(f"{sym.reference}: Datasheet already set")
            continue
        if sym.datasheet.strip() == url:
            skipped.append(f"{sym.reference}: already {url[:60]}")
            continue

        sch_path = (project_root / sym.sheet_path).resolve()
        if not sch_path.is_file():
            skipped.append(f"{sym.reference}: schematic missing ({sym.sheet_path})")
            continue

        if sch_path not in file_cache:
            file_cache[sch_path] = sch_path.read_text(encoding="utf-8")
        new_content, changed = _update_datasheet_in_content(
            file_cache[sch_path],
            sym.reference,
            url,
        )
        if not changed:
            skipped.append(f"{sym.reference}: could not update schematic")
            continue
        file_cache[sch_path] = new_content
        dirty_files.add(sch_path)
        updated.append(
            DatasheetFieldUpdate(
                sheet_path=sym.sheet_path,
                reference=sym.reference,
                part=sym_part,
                old_value=sym.datasheet,
                new_url=url,
            )
        )

    for path in dirty_files:
        path.write_text(file_cache[path], encoding="utf-8")

    return DatasheetFieldWriteResult(updated=updated, skipped=skipped)


# --- Spice field writeback (SUBCKT hookup) ---


@dataclass
class SpiceFieldUpdate:
    """One symbol Spice property batch written to a schematic file."""

    sheet_path: str
    reference: str
    part: str
    spice_model: str
    spice_lib: str
    spice_primitive: str
    sim_name: str = ""
    sim_pins: str = ""


@dataclass
class SimulationHookupSpec:
    """Resolved simulation model hookup for one part Value."""

    hookup_kind: str = "subckt"
    spice_model: str = ""
    spice_lib: str = ""
    spice_primitive: str = ""
    sim_device: str = ""
    sim_type: str = ""
    sim_name: str = ""
    sim_pins: str = ""
    sim_params: str = ""
    sim_library: str = ""
    lib_path: Path | None = None

    @classmethod
    def from_builtin(cls, hookup: BuiltinSimHookup) -> SimulationHookupSpec:
        return cls(
            hookup_kind="builtin",
            spice_model=hookup.spice_model,
            spice_primitive=hookup.spice_primitive,
            sim_device=hookup.sim_device,
            sim_type=hookup.sim_type,
            sim_pins=hookup.sim_pins,
            sim_params=hookup.sim_params,
        )

    @classmethod
    def from_subckt(
        cls,
        *,
        spice_model: str,
        spice_lib: str,
        spice_primitive: str,
        sim_name: str,
        sim_pins: str,
        lib_path: Path,
    ) -> SimulationHookupSpec:
        return cls(
            hookup_kind="subckt",
            spice_model=spice_model,
            spice_lib=spice_lib,
            spice_primitive=spice_primitive,
            sim_device="SUBCKT",
            sim_name=sim_name,
            sim_pins=sim_pins,
            sim_library=spice_lib,
            lib_path=lib_path,
        )


@dataclass
class SpiceFieldWriteResult:
    updated: list[SpiceFieldUpdate]
    skipped: list[str]

    @property
    def changed_count(self) -> int:
        return len(self.updated)


def _find_property_block_span(block: str, property_name: str) -> tuple[int, int] | None:
    """Return [start, end) slice for one ``(property "name" ...)`` s-expression."""
    marker = f'(property "{property_name}"'
    start = block.find(marker)
    if start == -1:
        return None
    depth = 0
    for pos in range(start, len(block)):
        ch = block[pos]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return start, pos + 1
    return None


def _property_pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        rf'\(property\s+"{re.escape(name)}"\s+"((?:[^"\\]|\\.)*)"(?:\s*\(at[^)]*\))*\s*\)',
        re.DOTALL,
    )


def _replace_or_insert_property(
    block: str,
    property_name: str,
    value: str,
) -> tuple[str, bool]:
    escaped = _escape_sch_property_value(value)
    span = _find_property_block_span(block, property_name)
    if span is not None:
        start, end = span
        prop_block = block[start:end]
        at_match = re.search(r"(\(at[^)]*\))", prop_block)
        at_clause = at_match.group(1) if at_match else "(at 0 0 0)"
        new_prop = f'(property "{property_name}" "{escaped}"\n      {at_clause}\n    )'
        new_block = block[:start] + new_prop + block[end:]
        return new_block, new_block != block

    value_match = re.search(
        r'(\(property\s+"Value"\s+"[^"]*"(?:\s*\(at[^)]*\))?\s*\))',
        block,
        re.DOTALL,
    )
    insert = f'\n    (property "{property_name}" "{escaped}"\n      (at 0 0 0)\n    )'
    if value_match:
        pos = value_match.end()
        new_block = block[:pos] + insert + block[pos:]
        return new_block, True
    closing = block.rfind(")")
    if closing == -1:
        return block, False
    new_block = block[:closing] + insert + block[closing:]
    return new_block, True


def _remove_property(block: str, property_name: str) -> tuple[str, bool]:
    span = _find_property_block_span(block, property_name)
    if span is None:
        return block, False
    start, end = span
    return block[:start] + block[end:], True


def _remove_all_properties(block: str, property_name: str) -> tuple[str, bool]:
    changed = False
    while True:
        block, removed = _remove_property(block, property_name)
        if not removed:
            break
        changed = True
    return block, changed


def _find_property_insert_anchor(block: str) -> int:
    """Position before first pin or instances child in a symbol block."""
    for pattern in (r"\n\s*\(pin", r"\n\s*\(instances"):
        match = re.search(pattern, block)
        if match:
            return match.start()
    return -1


def _symbol_property_indent_and_at(block: str) -> tuple[str, str]:
    """Match KiCad property formatting from the symbol's Value property."""
    match = re.search(
        r'\n(\s*)\(property\s+"Value"\s+"[^"]*"\s*(\(at[^)]*\))',
        block,
        re.DOTALL,
    )
    if match:
        return match.group(1), match.group(2)
    at_match = re.search(r"\(at\s+([^)]+)\)", block)
    if at_match:
        return "\t\t", f"(at {at_match.group(1)})"
    return "\t\t", "(at 0 0 0)"


def _insert_property_before_pins(block: str, property_name: str, value: str) -> tuple[str, bool]:
    escaped = _escape_sch_property_value(value)
    indent, at_clause = _symbol_property_indent_and_at(block)
    inner = indent + "\t"
    insert = (
        f'\n{indent}(property "{property_name}" "{escaped}"\n'
        f"{inner}{at_clause}\n"
        f"{inner}(hide yes)\n"
        f"{inner}(show_name no)\n"
        f"{inner}(do_not_autoplace no)\n"
        f"{inner}(effects\n"
        f"{inner}\t(font\n"
        f"{inner}\t\t(size 1.27 1.27)\n"
        f"{inner}\t)\n"
        f"{inner})\n"
        f"{indent})"
    )
    pos = _find_property_insert_anchor(block)
    if pos != -1:
        return block[:pos] + insert + block[pos:], True
    return _replace_or_insert_property(block, property_name, value)


def _set_property_on_block(
    block: str,
    property_name: str,
    value: str,
    *,
    insert_before_pins: bool = False,
) -> tuple[str, bool]:
    if insert_before_pins:
        new_block, _ = _remove_all_properties(block, property_name)
        return _insert_property_before_pins(new_block, property_name, value)
    prop_re = _property_pattern(property_name)
    if prop_re.search(block):
        return _replace_or_insert_property(block, property_name, value)
    return _replace_or_insert_property(block, property_name, value)


def resolve_simulation_hookup_for_symbol(
    sym: SymbolInstance,
    *,
    lib_path: Path,
    schematic_content: str,
    preferred_subckt_name: str | None = None,
) -> SimulationHookupSpec:
    """Build legacy Spice_* and KiCad 9 Sim.* values for one symbol."""
    lib_file = lib_path.expanduser().resolve()
    subckt_name, subckt_pins = load_subckt_metadata(
        lib_file,
        preferred_subckt_name or sym.spice_model or sym.value or sym.reference,
    )
    pin_names = parse_lib_symbol_pin_names(schematic_content, sym.lib_id)
    sim_pins = build_sim_pins_mapping(pin_names, subckt_pins)
    lib_str = str(lib_file)
    return SimulationHookupSpec.from_subckt(
        spice_model=subckt_name,
        spice_lib=lib_str,
        spice_primitive="X",
        sim_name=subckt_name,
        sim_pins=sim_pins,
        lib_path=lib_file,
    )


def simulation_hookup_needs_repair(sym: SymbolInstance) -> bool:
    """True when Spice_Lib is set but KiCad 9 Sim.* file hookup is incomplete."""
    lib_path = sym.spice_lib.strip() or sym.sim_library.strip()
    return kicad9_sim_hookup_incomplete(
        spice_lib=lib_path,
        sim_library=sym.sim_library,
        sim_device=sym.sim_device,
        sim_name=sym.sim_name,
        sim_params=sym.sim_params,
        sim_pins=sym.sim_pins,
    )


def _update_spice_in_content(
    content: str,
    reference: str,
    *,
    hookup: SimulationHookupSpec,
) -> tuple[str, bool]:
    ref_norm = reference.strip()
    changed = False
    parts: list[str] = []
    last = 0
    for block in _extract_symbol_blocks(content):
        start = content.find(block, last)
        if start == -1:
            continue
        end = start + len(block)
        props = _read_properties(block)
        if props.get("Reference", "").strip() != ref_norm:
            parts.append(content[last:end])
            last = end
            continue
        new_block = block
        if hookup.hookup_kind == "builtin":
            legacy_fields = (
                ("Spice_Model", hookup.spice_model),
                ("Spice_Primitive", hookup.spice_primitive),
            )
            kicad9_fields = (
                ("Sim.Device", hookup.sim_device),
                ("Sim.Type", hookup.sim_type),
                ("Sim.Pins", hookup.sim_pins),
                ("Sim.Params", hookup.sim_params),
            )
            for name in ("Spice_Lib", "Sim.Library", "Sim.Name"):
                new_block, removed = _remove_all_properties(new_block, name)
                changed = changed or removed
        else:
            legacy_fields = (
                ("Spice_Model", hookup.spice_model),
                ("Spice_Lib", hookup.spice_lib),
                ("Spice_Primitive", hookup.spice_primitive),
            )
            kicad9_fields = (
                ("Sim.Device", "SUBCKT"),
                ("Sim.Library", hookup.spice_lib),
                ("Sim.Name", hookup.sim_name),
                ("Sim.Pins", hookup.sim_pins),
            )
            new_block, removed = _remove_all_properties(new_block, "Sim.Params")
            changed = changed or removed
        for name, val in legacy_fields:
            new_block, block_changed = _set_property_on_block(
                new_block,
                name,
                val,
                insert_before_pins=True,
            )
            changed = changed or block_changed
        for name, val in kicad9_fields:
            if not val:
                if name == "Sim.Pins" and hookup.hookup_kind == "subckt":
                    continue
                continue
            new_block, block_changed = _set_property_on_block(
                new_block,
                name,
                val,
                insert_before_pins=True,
            )
            changed = changed or block_changed
        parts.append(content[last:start])
        parts.append(new_block)
        last = end
    parts.append(content[last:])
    if not changed:
        return content, False
    return "".join(parts), True


def write_spice_fields_for_part(
    project_pro_path: Path,
    ctx: ProjectContext,
    *,
    part: str,
    spice_model: str | None = None,
    spice_lib: str | None = None,
    spice_primitive: str = "X",
    hookup: SimulationHookupSpec | None = None,
) -> SpiceFieldWriteResult:
    """Write Spice_* and KiCad 9 Sim.* fields for all refs with this Value."""
    pro_path = project_pro_path.expanduser().resolve()
    project_root = pro_path.parent
    part_norm = part.strip()
    updated: list[SpiceFieldUpdate] = []
    skipped: list[str] = []
    file_cache: dict[Path, str] = {}
    dirty_files: set[Path] = set()

    for sym in ctx.symbols:
        sym_part = (sym.value or sym.reference).strip()
        if sym_part != part_norm:
            continue
        sch_path = (project_root / sym.sheet_path).resolve()
        if not sch_path.is_file():
            skipped.append(f"{sym.reference}: schematic missing ({sym.sheet_path})")
            continue
        if sch_path not in file_cache:
            file_cache[sch_path] = sch_path.read_text(encoding="utf-8")
        if hookup is not None:
            spec = hookup
        else:
            lib_str = (spice_lib or sym.spice_lib).strip()
            if not lib_str:
                skipped.append(f"{sym.reference}: no .lib path available")
                continue
            spec = resolve_simulation_hookup_for_symbol(
                sym,
                lib_path=Path(lib_str),
                schematic_content=file_cache[sch_path],
                preferred_subckt_name=spice_model or sym.spice_model or part_norm,
            )
        new_content, changed = _update_spice_in_content(
            file_cache[sch_path],
            sym.reference,
            hookup=spec,
        )
        if not changed:
            skipped.append(f"{sym.reference}: could not update simulation fields")
            continue
        file_cache[sch_path] = new_content
        dirty_files.add(sch_path)
        updated.append(
            SpiceFieldUpdate(
                sheet_path=sym.sheet_path,
                reference=sym.reference,
                part=sym_part,
                spice_model=spec.spice_model,
                spice_lib=spec.spice_lib,
                spice_primitive=spec.spice_primitive,
                sim_name=spec.sim_name,
                sim_pins=spec.sim_pins,
            )
        )

    for path in dirty_files:
        path.write_text(file_cache[path], encoding="utf-8")

    return SpiceFieldWriteResult(updated=updated, skipped=skipped)


def apply_builtin_simulation_models(
    project_pro_path: Path,
    symbols: list[SymbolInstance],
) -> SpiceFieldWriteResult:
    """Write built-in KiCad simulation models for standard passives, diodes, etc."""
    pro_path = project_pro_path.expanduser().resolve()
    project_root = pro_path.parent
    updated: list[SpiceFieldUpdate] = []
    skipped: list[str] = []
    file_cache: dict[Path, str] = {}
    dirty_files: set[Path] = set()

    for sym in symbols:
        sch_path = (project_root / sym.sheet_path).resolve()
        if not sch_path.is_file():
            skipped.append(f"{sym.reference}: schematic missing ({sym.sheet_path})")
            continue
        if sch_path not in file_cache:
            file_cache[sch_path] = sch_path.read_text(encoding="utf-8")
        builtin = resolve_builtin_simulation_hookup(sym, file_cache[sch_path])
        if builtin is None:
            continue
        spec = SimulationHookupSpec.from_builtin(builtin)
        new_content, changed = _update_spice_in_content(
            file_cache[sch_path],
            sym.reference,
            hookup=spec,
        )
        if not changed:
            skipped.append(f"{sym.reference}: built-in model already set")
            continue
        file_cache[sch_path] = new_content
        dirty_files.add(sch_path)
        updated.append(
            SpiceFieldUpdate(
                sheet_path=sym.sheet_path,
                reference=sym.reference,
                part=(sym.value or sym.reference).strip(),
                spice_model=spec.spice_model,
                spice_lib=spec.spice_lib,
                spice_primitive=spec.spice_primitive,
                sim_name=spec.sim_name,
                sim_pins=spec.sim_pins,
            )
        )

    for path in dirty_files:
        path.write_text(file_cache[path], encoding="utf-8")

    return SpiceFieldWriteResult(updated=updated, skipped=skipped)


def format_builtin_sim_write_message(result: SpiceFieldWriteResult) -> str:
    """User-facing alert after Apply built-in models."""
    refs = ", ".join(u.reference for u in result.updated)
    sheets = sorted({u.sheet_path for u in result.updated})
    sheet_lines = "\n".join(f"  • {name}" for name in sheets)
    return (
        f"Applied built-in simulation models for: {refs}\n\n"
        f"{result.changed_count} symbol(s) updated.\n\n"
        f"Schematic file(s):\n{sheet_lines}\n\n"
        "If a sheet is open in KiCad's Schematic Editor, use File → Revert on "
        "the sheet(s) above to see updated Symbol Properties."
    )


def format_spice_write_success_message(result: SpiceFieldWriteResult) -> str:
    """User-facing alert after successful Apply Spice fields action."""
    refs = ", ".join(u.reference for u in result.updated)
    sheets = sorted({u.sheet_path for u in result.updated})
    sheet_lines = "\n".join(f"  • {name}" for name in sheets)
    first = result.updated[0]
    return (
        f"Updated simulation model for: {refs}\n\n"
        f"Sim.Device: SUBCKT\n"
        f"Sim.Name: {first.sim_name}\n"
        f"Sim.Library: {first.spice_lib}\n"
        f"Sim.Pins: {first.sim_pins or '(verify in KiCad Pin Assignments)'}\n\n"
        f"Legacy Spice_Model: {first.spice_model}\n"
        f"Legacy Spice_Lib: {first.spice_lib}\n\n"
        f"Schematic file(s):\n{sheet_lines}\n\n"
        "Open Symbol Properties → Simulation Model… to confirm "
        "\"SPICE model from file\" is selected.\n\n"
        "If a sheet is open in KiCad's Schematic Editor, the Spice properties "
        "will not update on screen until you reload from disk.\n\n"
        "To see the change without losing your work:\n"
        "1. Save the schematic in KiCad first if you have unsaved edits you want "
        "to keep.\n"
        "2. Do not use File → Save after this write — that can overwrite the new "
        "values still shown in the editor.\n"
        "3. In the Schematic Editor: File → Revert on the sheet(s) above, or "
        "close and reopen that schematic.\n\n"
        "File → Revert discards schematic changes made since your last save."
    )
