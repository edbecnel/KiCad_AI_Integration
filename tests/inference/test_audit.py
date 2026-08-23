"""Tests for one-click audit inference."""

from __future__ import annotations

from pathlib import Path

from context.model import ProjectContext
from inference.audit import run_pcb_layout_review, run_schematic_review
from providers.types import ProviderResponse, TokenUsage

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class _MockAuditProvider:
    def send_message(self, prompt: str, *, system=None, image=None, config=None, **kwargs):
        return ProviderResponse(
            text=(
                "Audit complete.\n\n```json\n"
                '{"findings": [{"id":"F1","severity":"critical","category":"clearance",'
                '"summary":"Tight spacing","recommendation":"Widen trace","references":["U1"]}]}\n'
                "```"
            ),
            model="mock-audit",
            usage=TokenUsage(100, 50),
        )


def test_run_schematic_review_persists_report(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    ctx = ProjectContext(project_path=str(pro), project_name="demo")
    result = run_schematic_review(ctx, provider=_MockAuditProvider(), persist=True)
    assert result.report.audit_type == "schematic_review"
    assert len(result.report.findings) == 1
    assert result.report_path is not None
    assert result.report_path.is_file()


def test_run_post_route_review_persists_report(tmp_path: Path) -> None:
    from inference.audit import run_post_route_review

    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    ctx = ProjectContext(project_path=str(pro), project_name="demo")

    class _MockProvider:
        def send_message(self, prompt: str, *, system=None, image=None, config=None, **kwargs):
            return ProviderResponse(
                text='{"findings": []}',
                model="mock",
                usage=TokenUsage(5, 3),
            )

    result = run_post_route_review(
        ctx,
        routing_result_summary={"success": True},
        quality_report={"notes": ["ok"]},
        provider=_MockProvider(),
        persist=True,
    )
    assert result.report.audit_type == "post_route_review"
    assert result.report_path is not None


def test_run_pcb_layout_review_no_persist(tmp_path: Path) -> None:
    pro = tmp_path / "demo.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    ctx = ProjectContext(project_path=str(pro), project_name="demo")
    result = run_pcb_layout_review(ctx, provider=_MockAuditProvider(), persist=False)
    assert result.report.audit_type == "pcb_layout_review"
    assert result.report_path is None
