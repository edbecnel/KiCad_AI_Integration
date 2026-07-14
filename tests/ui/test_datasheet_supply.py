"""Tests for datasheet supply UI helpers (headless)."""

from pathlib import Path

from context.schematic_parse import SymbolInstance
from ui.datasheet_supply import (
    MissingDatasheetRow,
    attach_datasheet_pdf,
    get_missing_datasheet_rows,
    manual_pdf_path_for_part,
)
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_manual_pdf_path_for_part() -> None:
    lib = Path("/tmp/lib")
    assert manual_pdf_path_for_part(lib, "FOD3180") == lib / "datasheets" / "FOD3180.pdf"


def test_missing_row_from_summary_includes_url() -> None:
    symbols = [
        SymbolInstance(
            reference="U1",
            value="LM7805",
            datasheet="https://example.com/lm7805.pdf",
            sheet_path="p.kicad_sch",
        )
    ]
    entry = {
        "part": "LM7805",
        "references": ["U1"],
        "reference_count": 1,
        "status": "fetch_failed",
        "errors": ["timeout"],
    }
    row = MissingDatasheetRow.from_summary_entry(entry, symbols)
    assert row.symbol_datasheet_url == "https://example.com/lm7805.pdf"
    assert row.errors == ["timeout"]


def test_get_missing_datasheet_rows_empty_when_resolved(tmp_path: Path) -> None:
    pro = FIXTURES / "testproj.kicad_pro"
    lib = tmp_path / "lib"
    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="never")
    ctx, rows = get_missing_datasheet_rows(pro, config=config, verbose=False)
    assert ctx.project_name == "testproj"
    assert isinstance(rows, list)


def test_attach_datasheet_pdf_registers_part(tmp_path: Path) -> None:
    pro = FIXTURES / "testproj.kicad_pro"
    lib = tmp_path / "lib"
    pdf = FIXTURES / "datasheets" / "F0D3180.pdf"
    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="never")
    ctx = attach_datasheet_pdf(pro, "F0D3180", pdf, config=config, verbose=False)
    res = ctx.datasheet_resolutions.get("U3")
    assert res is not None
    assert res.status == "resolved"
    assert (lib / "datasheets" / "F0D3180.pdf").is_file()


def test_attach_same_pdf_for_alias_part_resolves_via_manifest(tmp_path: Path) -> None:
    """Resolver must resolve alias Value when manifest links it to an existing PDF artifact."""
    from context.artifacts.catalog import ComponentRef
    from context.artifacts.store import ArtifactStore, ProjectContextInfo
    from context.datasheet_resolver import DatasheetResolver

    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    sch = tmp_path / "p.kicad_sch"
    sch.touch()
    lib = tmp_path / "lib"
    store = ArtifactStore(lib)
    pdf = tmp_path / "FOD3180.pdf"
    pdf.write_bytes(b"%PDF-1.4 fod3180")
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[sch])

    store.register_datasheet(
        pdf,
        "FOD3180",
        "user_attach",
        project,
        ComponentRef(reference="U1", sheet_path="p.kicad_sch"),
    )
    store.register_datasheet(
        pdf,
        "FOD3180-TEST",
        "user_attach",
        project,
        ComponentRef(reference="U14", sheet_path="p.kicad_sch"),
    )

    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="never")
    resolver = DatasheetResolver(config, store=store, verbose=False)
    symbol = SymbolInstance(
        reference="U14",
        value="FOD3180-TEST",
        datasheet="https://example.invalid/fod3180.pdf",
        sheet_path="p.kicad_sch",
    )
    result = resolver.resolve_all([symbol], project)["U14"]
    assert result.status == "resolved"
    assert result.artifact_id is not None
