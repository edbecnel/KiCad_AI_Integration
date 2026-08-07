"""End-to-end chat pipeline test with mocked provider."""

from __future__ import annotations

from pathlib import Path

from context.collector import collect_stretch_context
from inference.chat import build_chat_prompt, send_chat_prompt
from providers.types import ProviderResponse, TokenUsage

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class _MockChatProvider:
    def send_message(self, prompt: str, *, system=None, image=None, config=None, **kwargs):
        return ProviderResponse(
            text="Mock analysis complete.",
            model="mock",
            usage=TokenUsage(10, 5),
        )


def test_chat_pipeline_general_review_mock_provider(tmp_path) -> None:
    ds_dir = FIXTURES / "datasheets"
    ds_dir.mkdir(exist_ok=True)
    (ds_dir / "F0D3180.pdf").write_bytes(b"%PDF-1.4 test")

    from utils.config import AppConfig

    config = AppConfig(artifact_library_path=tmp_path / "library")
    ctx = collect_stretch_context(
        FIXTURES / "testproj.kicad_pro",
        config=config,
        include_image=False,
        verbose=False,
    )
    built = build_chat_prompt(ctx, "Summarize active parts.", template="general_review")
    assert built.template == "general_review"
    result = send_chat_prompt(built, ctx, provider=_MockChatProvider())
    assert "Mock analysis" in result.response.text


def test_chat_pipeline_netlist_crosscheck_mock_provider() -> None:
    from context.model import ProjectContext

    ctx = ProjectContext(
        project_path="/tmp/p",
        project_name="demo",
        schematic_connectivity={"unique_net_names": ["VCC"]},
        connectivity_graph={
            "nets": ["VCC"],
            "connections": [],
            "connection_count": 0,
            "auto_generated_nets": [],
            "include_paths": [],
        },
    )
    built = build_chat_prompt(ctx, "Verify netlist.", template="netlist_crosscheck")
    assert built.template == "netlist_crosscheck"
    result = send_chat_prompt(built, ctx, provider=_MockChatProvider())
    assert result.response.usage.output_tokens == 5
