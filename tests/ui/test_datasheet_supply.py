"""Tests for datasheet supply UI helpers (headless)."""

from pathlib import Path
from unittest.mock import patch

from context.artifacts.ai_discovery_log import AiDiscoveryLog
from context.artifacts.store import ArtifactStore
from context.schematic_parse import SymbolInstance
from context.schematic_write import DatasheetFieldUpdate, DatasheetFieldWriteResult
from ui.datasheet_supply import (
    MissingDatasheetRow,
    attach_datasheet_pdf,
    enrich_rows_from_discovery_log,
    format_row_detail_text,
    format_write_url_success_message,
    get_missing_datasheet_rows,
    manual_pdf_path_for_part,
    run_ai_discovery_for_rows,
)
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_manual_pdf_path_for_part() -> None:
    lib = Path("/tmp/lib")
    assert manual_pdf_path_for_part(lib, "FOD3180") == lib / "datasheets" / "FOD3180.pdf"


def test_format_write_url_success_message_includes_reload_guidance() -> None:
    result = DatasheetFieldWriteResult(
        updated=[
            DatasheetFieldUpdate(
                sheet_path="power.kicad_sch",
                reference="U3",
                part="FOD3180",
                old_value="",
                new_url="https://example.com/fod3180.pdf",
            )
        ],
        skipped=[],
    )
    message = format_write_url_success_message(result)
    assert "U3" in message
    assert "https://example.com/fod3180.pdf" in message
    assert "power.kicad_sch" in message
    assert "File → Revert" in message
    assert "Do not use File → Save" in message


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


def test_get_missing_skips_ai_discovery_when_config_enabled(tmp_path: Path) -> None:
    pro = FIXTURES / "testproj.kicad_pro"
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_url_fetch="never",
        datasheet_ai_discovery=True,
    )
    with patch("context.ai_datasheet_discovery.run_ai_datasheet_discovery") as mock_ai:
        get_missing_datasheet_rows(pro, config=config, verbose=False)
    mock_ai.assert_not_called()


def test_enrich_rows_from_stale_fetch_not_attempted_log(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "lib")
    store.ai_discovery_log.record_attempt(
        "BD243C",
        suggested_urls=["https://www.onsemi.com/download/data-sheet/pdf/bd243c-d.pdf"],
        outcome="no_url_found",
        error="AI suggested URLs (fetch not attempted — enable --ai-datasheets-auto-fetch)",
    )
    row = MissingDatasheetRow(
        part="BD243C",
        references=["Q1"],
        reference_count=1,
        status="fetch_failed",
        errors=[],
    )
    enrich_rows_from_discovery_log([row], store)
    assert row.suggested_urls[0].endswith("bd243c-d.pdf")
    assert row.discovery_status == "AI URL ready"


def test_format_row_detail_text_includes_full_suggested_url() -> None:
    row = MissingDatasheetRow(
        part="BD243C",
        references=["Q1"],
        reference_count=1,
        status="fetch_failed",
        errors=[],
        suggested_urls=["https://www.onsemi.com/download/data-sheet/pdf/bd243c-d.pdf"],
    )
    text = format_row_detail_text(row)
    assert "bd243c-d.pdf" in text
    assert "Suggested:" in text or "bd243c-d.pdf" in text


def test_format_row_detail_text_includes_fetch_attempts() -> None:
    row = MissingDatasheetRow(
        part="BD243C",
        references=["Q1"],
        reference_count=1,
        status="fetch_failed",
        errors=[],
        suggested_urls=[
            "https://www.onsemi.com/a.pdf",
            "https://www.onsemi.com/b.pdf",
        ],
        fetch_attempts=[
            ("https://www.onsemi.com/a.pdf", "bot protection"),
        ],
    )
    text = format_row_detail_text(row)
    assert "FAIL" in text
    assert "b.pdf" in text


def test_run_ai_discovery_requires_approval_or_auto_fetch(tmp_path: Path) -> None:
    pro = FIXTURES / "testproj.kicad_pro"
    config = AppConfig(
        artifact_library_path=tmp_path / "lib",
        datasheet_ai_discovery_auto_fetch=False,
    )
    try:
        run_ai_discovery_for_rows(pro, config=config, verbose=False)
    except ValueError as exc:
        assert "approve" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError when no approval path")


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


def test_attach_replaces_stale_catalog_entry_without_file(tmp_path: Path) -> None:
    """Attach must work when catalog has a part entry whose PDF file was removed."""
    from context.artifacts.catalog import ComponentRef
    from context.artifacts.store import ArtifactStore, ProjectContextInfo

    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    sch = tmp_path / "p.kicad_sch"
    sch_content = """
(kicad_sch (version 20230121) (generator "test")
  (symbol (lib_id "x:FOD3180") (at 0 0 0) (unit 1)
    (property "Reference" "U1" (at 0 0 0))
    (property "Value" "FOD3180" (at 0 0 0))
    (property "Datasheet" "https://example.invalid/fod3180.pdf" (at 0 0 0))
  )
)
"""
    sch.write_text(sch_content, encoding="utf-8")
    lib = tmp_path / "lib"
    config = AppConfig(artifact_library_path=lib, datasheet_url_fetch="if_missing")

    store = ArtifactStore(lib)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[sch])
    stale_pdf = tmp_path / "stale.pdf"
    stale_pdf.write_bytes(b"%PDF-1.4 stale")
    entry = store.register_datasheet(
        stale_pdf,
        "FOD3180",
        "https_fetch",
        project,
        ComponentRef(reference="U1", sheet_path="p.kicad_sch"),
        source_url="https://example.invalid/fod3180.pdf",
    )
    (lib / "datasheets" / "FOD3180.pdf").unlink()
    assert store.resolve_local_path(entry.id) is None

    user_pdf = tmp_path / "FOD3180-1008860.pdf"
    user_pdf.write_bytes(b"%PDF-1.4 user downloaded")

    ctx = attach_datasheet_pdf(pro, "FOD3180", user_pdf, config=config, verbose=False)
    res = ctx.datasheet_resolutions["U1"]
    assert res.status == "resolved"
    assert (lib / "datasheets" / "FOD3180.pdf").is_file()
    assert res.local_path is not None
    assert res.local_path.name == "FOD3180.pdf"
