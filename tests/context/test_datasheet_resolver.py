"""Tests for datasheet resolver."""

from pathlib import Path

from context.artifacts.store import ProjectContextInfo
from context.datasheet_resolver import DatasheetResolver
from context.schematic_parse import SymbolInstance
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_local_datasheet_field_registers_in_catalog(tmp_path: Path) -> None:
    project_root = FIXTURES
    pro = project_root / "testproj.kicad_pro"
    ds_dir = project_root / "datasheets"
    ds_dir.mkdir(exist_ok=True)
    pdf = ds_dir / "F0D3180.pdf"
    pdf.write_bytes(b"%PDF-1.4 test datasheet")

    lib_path = tmp_path / "library"
    config = AppConfig(artifact_library_path=lib_path, datasheet_url_fetch="if_missing")
    resolver = DatasheetResolver(config)

    project = ProjectContextInfo(
        project_pro_path=pro,
        schematic_paths=[project_root / "testproj.kicad_sch"],
    )
    symbol = SymbolInstance(
        reference="U3",
        value="F0D3180",
        datasheet="datasheets/F0D3180.pdf",
        sheet_path="testproj.kicad_sch",
    )
    result = resolver.resolve_symbol(symbol, project)
    assert result.status == "resolved"
    assert result.tier_hint == "A"
    assert result.artifact_id is not None
    assert result.local_path is not None
    assert (lib_path / "datasheets" / "F0D3180.pdf").is_file()


def test_missing_datasheet_tier_b(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(artifact_library_path=tmp_path / "lib", datasheet_url_fetch="if_missing")
    resolver = DatasheetResolver(config)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    symbol = SymbolInstance(
        reference="U3",
        value="F0D3180",
        footprint="DIP-6",
        sheet_path="p.kicad_sch",
    )
    result = resolver.resolve_symbol(symbol, project)
    assert result.status == "missing"
    assert result.tier_hint == "B"


def test_https_fetch_registers_pdf(tmp_path: Path) -> None:
    pro = tmp_path / "p.kicad_pro"
    pro.touch()
    config = AppConfig(artifact_library_path=tmp_path / "lib", datasheet_url_fetch="if_missing")

    def fake_fetch(url, dest, **kwargs):
        dest.write_bytes(b"%PDF-1.4 fetched")
        from utils.url_fetch import FetchResult

        return FetchResult(path=dest, content_type="application/pdf", byte_size=14)

    resolver = DatasheetResolver(config, fetch_fn=fake_fetch)
    project = ProjectContextInfo(project_pro_path=pro, schematic_paths=[])
    symbol = SymbolInstance(
        reference="U1",
        value="LM7805",
        datasheet="https://example.com/lm7805.pdf",
        sheet_path="p.kicad_sch",
    )
    result = resolver.resolve_symbol(symbol, project)
    assert result.status == "resolved"
    assert result.tier_hint == "A"
