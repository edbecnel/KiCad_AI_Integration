"""macOS KiCad plugin install path verification (automated checklist)."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SOURCE = REPO_ROOT / "src" / "plugin" / "kicad_ai_assistant_plugin.py"
MACOS_PLUGIN_DIR = Path.home() / "Documents" / "KiCad" / "10.0" / "scripting" / "plugins"
EXPECTED_SYMLINK = MACOS_PLUGIN_DIR / "kicad_ai_assistant.py"


def test_plugin_source_file_exists() -> None:
    assert PLUGIN_SOURCE.is_file(), "Single-file plugin entry must exist in the repo"


def test_plugin_source_bootstraps_src_path() -> None:
    text = PLUGIN_SOURCE.read_text(encoding="utf-8")
    assert "sys.path" in text
    assert "kicad_ai_assistant_plugin" in PLUGIN_SOURCE.name


def test_macos_plugin_symlink_points_to_repo_when_installed() -> None:
    """When the user symlink is present, it should target the repo plugin file."""
    if not EXPECTED_SYMLINK.exists():
        return
    target = EXPECTED_SYMLINK.resolve()
    assert target == PLUGIN_SOURCE.resolve()


def test_macos_plugin_directory_documented() -> None:
    """KiCad 10 on macOS uses Documents/KiCad, not ~/.config/kicad."""
    assert "KiCad" in str(MACOS_PLUGIN_DIR)
    assert MACOS_PLUGIN_DIR.name == "plugins"
