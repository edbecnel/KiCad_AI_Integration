"""Pytest configuration."""

import sys
from pathlib import Path

import pytest

from utils.config import AppConfig

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live: tests that call external APIs (skipped unless ANTHROPIC_API_KEY is set)",
    )
    config.addinivalue_line(
        "markers",
        "kicad: tests that require KiCad pcbnew or kicad-cli (optional manual runs)",
    )


@pytest.fixture
def isolated_library_config(tmp_path: Path) -> AppConfig:
    """AppConfig with artifact library confined to tmp_path (no writes outside workspace)."""
    return AppConfig(artifact_library_path=tmp_path / "kicad_ai_library")


@pytest.fixture
def blocking_oscillator_pro() -> Path:
    return FIXTURES / "blocking_oscillator.kicad_pro"


def _install_mock_pcbnew() -> None:
    """Provide a minimal pcbnew stub when KiCad is not installed."""
    if "pcbnew" in sys.modules:
        return
    import types

    pcbnew = types.ModuleType("pcbnew")

    class _Board:
        def GetFootprints(self):
            return []

        def GetFileName(self) -> str:
            return ""

    def GetBoard():
        return None

    pcbnew.GetBoard = GetBoard
    sys.modules["pcbnew"] = pcbnew


_install_mock_pcbnew()
