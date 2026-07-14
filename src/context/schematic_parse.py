"""Minimal .kicad_sch S-expression parser for symbol properties."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SymbolInstance:
    reference: str
    value: str
    datasheet: str = ""
    footprint: str = ""
    spice_model: str = ""
    spice_lib: str = ""
    spice_primitive: str = ""
    sheet_path: str = ""
    sheet_name: str = "/"
    lib_id: str = ""
    custom_fields: dict[str, str] = field(default_factory=dict)


@dataclass
class SheetRef:
    sheet_name: str
    sheet_file: str


def _read_properties(symbol_block: str) -> dict[str, str]:
    props: dict[str, str] = {}
    pattern = re.compile(
        r'\(property\s+"([^"]+)"\s+"([^"]*)"',
        re.DOTALL,
    )
    for match in pattern.finditer(symbol_block):
        props[match.group(1)] = match.group(2)
    return props


def _is_lib_symbol_definition(block: str) -> bool:
    """True for (symbol \"Lib:Name\" ...) entries inside lib_symbols, not placed instances."""
    rest = block[len("(symbol") :].lstrip()
    return rest.startswith('"')


def _extract_symbol_blocks(content: str) -> list[str]:
    """Return raw (symbol ...) blocks, excluding the lib_symbols section."""
    lib_start = content.find("(lib_symbols")
    search_regions: list[str] = []
    if lib_start == -1:
        search_regions.append(content)
    else:
        depth = 0
        lib_end = lib_start
        for pos in range(lib_start, len(content)):
            if content[pos] == "(":
                depth += 1
            elif content[pos] == ")":
                depth -= 1
                if depth == 0:
                    lib_end = pos + 1
                    break
        search_regions.append(content[:lib_start])
        search_regions.append(content[lib_end:])

    blocks: list[str] = []
    for region in search_regions:
        idx = 0
        while True:
            start = region.find("(symbol", idx)
            if start == -1:
                break
            depth = 0
            end = start
            for pos in range(start, len(region)):
                if region[pos] == "(":
                    depth += 1
                elif region[pos] == ")":
                    depth -= 1
                    if depth == 0:
                        end = pos + 1
                        break
            block = region[start:end]
            if not _is_lib_symbol_definition(block):
                blocks.append(block)
            idx = end
    return blocks


def _extract_sheets(content: str) -> list[SheetRef]:
    sheets: list[SheetRef] = []
    idx = 0
    while True:
        start = content.find("(sheet", idx)
        if start == -1:
            break
        depth = 0
        end = start
        for pos in range(start, len(content)):
            if content[pos] == "(":
                depth += 1
            elif content[pos] == ")":
                depth -= 1
                if depth == 0:
                    end = pos + 1
                    break
        block = content[start:end]
        props = _read_properties(block)
        sheet_file = props.get("Sheetfile", "")
        sheet_name = props.get("Sheetname", props.get("Sheet name", ""))
        if sheet_file:
            sheets.append(SheetRef(sheet_name=sheet_name, sheet_file=sheet_file))
        idx = end
    return sheets


def _lib_id_from_block(block: str) -> str:
    match = re.search(r'\(lib_id\s+"([^"]+)"\)', block)
    return match.group(1) if match else ""


def parse_schematic_symbols(
    schematic_path: Path,
    *,
    sheet_name: str = "/",
) -> list[SymbolInstance]:
    """Parse symbol instances from a single .kicad_sch file."""
    content = schematic_path.expanduser().read_text(encoding="utf-8")
    sheet_path = schematic_path.name
    symbols: list[SymbolInstance] = []

    for block in _extract_symbol_blocks(content):
        props = _read_properties(block)
        reference = props.get("Reference", "")
        if not reference:
            continue
        standard = {
            "Reference",
            "Value",
            "Datasheet",
            "Footprint",
            "Spice_Model",
            "Spice_Lib",
            "Spice_Primitive",
        }
        custom = {k: v for k, v in props.items() if k not in standard}
        symbols.append(
            SymbolInstance(
                reference=reference,
                value=props.get("Value", ""),
                datasheet=props.get("Datasheet", ""),
                footprint=props.get("Footprint", ""),
                spice_model=props.get("Spice_Model", ""),
                spice_lib=props.get("Spice_Lib", ""),
                spice_primitive=props.get("Spice_Primitive", ""),
                sheet_path=sheet_path,
                sheet_name=sheet_name,
                lib_id=_lib_id_from_block(block),
                custom_fields=custom,
            )
        )
    return symbols


def parse_project_schematics(
    project_root: Path,
    schematic_paths: list[Path],
    root_schematic: Path | None = None,
) -> list[SymbolInstance]:
    """
    Parse symbols from listed schematics plus one level of hierarchical subsheets.
    """
    all_symbols: list[SymbolInstance] = []
    parsed_files: set[str] = set()

    def parse_file(sch_path: Path, sheet_name: str) -> None:
        resolved = sch_path if sch_path.is_absolute() else project_root / sch_path
        key = str(resolved.resolve())
        if key in parsed_files or not resolved.is_file():
            return
        parsed_files.add(key)
        symbols = parse_schematic_symbols(resolved, sheet_name=sheet_name)
        all_symbols.extend(symbols)
        content = resolved.read_text(encoding="utf-8")
        for sheet in _extract_sheets(content):
            sub_path = project_root / sheet.sheet_file
            parse_file(sub_path, sheet.sheet_name or sheet.sheet_file)

    if root_schematic is not None:
        parse_file(root_schematic, "/")
    else:
        for sch in schematic_paths:
            parse_file(sch, "/")

    return all_symbols


def discover_schematic_paths(project_pro_path: Path) -> list[Path]:
    """Return schematic paths for a project (root .kicad_sch matching project name)."""
    pro = project_pro_path.expanduser().resolve()
    root = pro.parent
    default_sch = root / f"{pro.stem}.kicad_sch"
    if default_sch.is_file():
        return [default_sch]
    return sorted(root.glob("*.kicad_sch"))
