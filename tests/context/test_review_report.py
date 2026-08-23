"""Tests for structured review reports."""

from __future__ import annotations

import json
from pathlib import Path

from context.review_report import (
    ReviewFinding,
    ReviewReport,
    parse_findings_from_response,
    reviews_dir,
    save_review_report,
)
from providers.types import TokenUsage


def test_parse_findings_from_fenced_json() -> None:
    text = (
        "Here is my review.\n\n"
        "```json\n"
        '{"findings": [{"id":"F1","severity":"warning","category":"netlist",'
        '"summary":"Missing pull-up","recommendation":"Add 10k","references":["R3"]}]}\n'
        "```"
    )
    findings = parse_findings_from_response(text)
    assert len(findings) == 1
    assert findings[0].severity == "warning"
    assert findings[0].references == ["R3"]


def test_save_review_report_round_trip(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    report = ReviewReport(
        audit_type="schematic_review",
        project_path=str(pro),
        model="mock",
        findings=[
            ReviewFinding(
                id="F1",
                severity="info",
                category="general",
                summary="ok",
                recommendation="none",
            )
        ],
        narrative="done",
        usage=TokenUsage(1, 2),
    )
    path = save_review_report(report)
    assert path.is_file()
    assert path.parent == reviews_dir(pro)
    loaded = ReviewReport.from_dict(json.loads(path.read_text(encoding="utf-8")))
    assert loaded.audit_type == "schematic_review"
    assert loaded.findings[0].summary == "ok"
