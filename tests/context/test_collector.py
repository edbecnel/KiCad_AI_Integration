"""Integration test for stretch context collection."""

import json
from pathlib import Path

from context.collector import collect_stretch_context
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
GOLDEN = Path(__file__).resolve().parent / "golden" / "stretch_context_summary.json"


def _redact_paths(data: dict) -> dict:
    """Remove machine-specific paths for golden comparison."""
    out = json.loads(json.dumps(data))
    if out.get("project_path"):
        out["project_path"] = "<PROJECT>"
    if out.get("artifact_manifest_path"):
        out["artifact_manifest_path"] = "<MANIFEST>"
    for ref, res in out.get("datasheet_resolutions", {}).items():
        if res.get("local_path"):
            res["local_path"] = "<LOCAL_PATH>"
        if res.get("artifact_id"):
            res["artifact_id"] = "<ARTIFACT_ID>"
    return out


def test_collect_stretch_context_golden(tmp_path: Path) -> None:
    ds_dir = FIXTURES / "datasheets"
    ds_dir.mkdir(exist_ok=True)
    (ds_dir / "F0D3180.pdf").write_bytes(b"%PDF-1.4 golden test")

    config = AppConfig(artifact_library_path=tmp_path / "library")
    ctx = collect_stretch_context(
        FIXTURES / "testproj.kicad_pro",
        config=config,
        include_image=False,
    )
    summary = _redact_paths(ctx.to_dict())
    summary["symbol_count"] = len(ctx.symbols)
    summary["resolved_count"] = sum(
        1 for r in ctx.datasheet_resolutions.values() if r.status == "resolved"
    )
    # Drop volatile symbol list details; keep counts and resolution statuses
    summary.pop("symbols", None)
    for res in summary.get("datasheet_resolutions", {}).values():
        res.pop("sources_tried", None)

    if not GOLDEN.is_file():
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(summary, indent=2) + "\n")

    expected = json.loads(GOLDEN.read_text())
    assert summary["project_name"] == expected["project_name"]
    assert summary["symbol_count"] == expected["symbol_count"]
    assert summary["resolved_count"] >= 1
    u3 = summary["datasheet_resolutions"].get("U3", {})
    assert u3.get("status") == "resolved"
    assert u3.get("tier_hint") == "A"
