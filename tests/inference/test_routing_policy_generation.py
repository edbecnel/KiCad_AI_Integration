"""Tests for routing policy generation orchestration."""

from __future__ import annotations

from pathlib import Path

from context.collector import collect_stretch_context
from inference.routing import run_routing_policy_generation
from routing.policy_store import routing_policy_file_path
from providers.types import ProviderResponse, TokenUsage


class _FakeProvider:
    def send_message(self, prompt, *, system=None, image=None, config=None):
        return ProviderResponse(
            text=(
                '{"net_classifications": ['
                '{"net_name": "SPI_MOSI", "classification": "ordinary_signal", "explain": "Safe"}'
                '], "notes": "Generated policy."}'
            ),
            model="test-model",
            usage=TokenUsage(input_tokens=10, output_tokens=20),
        )


def test_run_routing_policy_generation_persists(blocking_oscillator_pro: Path) -> None:
    ctx = collect_stretch_context(blocking_oscillator_pro)
    result = run_routing_policy_generation(ctx, provider=_FakeProvider())
    assert result.policy.notes == "Generated policy."
    assert len(result.policy.net_classifications) == 1
    assert result.saved_path == routing_policy_file_path(blocking_oscillator_pro)
    assert result.saved_path.is_file()
