"""Tests for KiCad ActionPlugin wiring."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_kicad_ai_assistant_plugin_metadata() -> None:
    from plugin.kicad_ai_assistant.action_plugin import KiCadAIAssistantPlugin

    plugin = KiCadAIAssistantPlugin()
    plugin.defaults()
    assert plugin.name == "KiCad AI Assistant"
    assert plugin.category == "AI Tools"
    assert plugin.show_toolbar_button is True
    assert "Assistant" in plugin.description


def test_ensure_src_on_path_finds_repo_src() -> None:
    from plugin.bootstrap import ensure_src_on_path

    root = ensure_src_on_path()
    assert root is not None
    assert (root / "ui").is_dir()


def test_kicad_plugin_package_imports_from_plugins_path_only(tmp_path: Path) -> None:
    """KiCad only adds scripting/plugins to sys.path — package must self-bootstrap src/."""
    import sys

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    target = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "plugin"
        / "kicad_ai_assistant"
    )
    link = plugins_dir / "kicad_ai_assistant"
    link.symlink_to(target, target_is_directory=True)

    saved_path = sys.path[:]
    saved_modules = {
        name: sys.modules[name]
        for name in list(sys.modules)
        if name == "kicad_ai_assistant" or name.startswith("kicad_ai_assistant.")
    }
    for name in saved_modules:
        del sys.modules[name]
    sys.path = [str(plugins_dir)]
    try:
        import kicad_ai_assistant  # noqa: F401
    finally:
        sys.path = saved_path
        for name in saved_modules:
            sys.modules[name] = saved_modules[name]


def test_kicad_single_file_plugin_imports_from_plugins_path(tmp_path: Path) -> None:
    import importlib.util
    import sys

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    source = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "plugin"
        / "kicad_ai_assistant_plugin.py"
    )
    link = plugins_dir / "kicad_ai_assistant.py"
    link.symlink_to(source)

    saved_path = sys.path[:]
    sys.path = [str(plugins_dir)]
    try:
        spec = importlib.util.spec_from_file_location("kicad_ai_assistant", link)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert any(Path(p).joinpath("ui").is_dir() for p in sys.path)
    finally:
        sys.path = saved_path


def test_plugin_run_opens_assistant_window(tmp_path: Path) -> None:
    pytest.importorskip("wx")
    import wx

    pro = tmp_path / "proj.kicad_pro"
    pro.write_text("{}", encoding="utf-8")
    pcb = tmp_path / "proj.kicad_pcb"
    pcb.write_text("", encoding="utf-8")

    app = wx.GetApp()
    if app is None:
        app = wx.App(False)

    parent = wx.Frame(None, title="pcb")
    parent.Show(False)

    from plugin.kicad_ai_assistant.action_plugin import KiCadAIAssistantPlugin

    plugin = KiCadAIAssistantPlugin()
    with patch("ui.launcher.resolve_project_pro_path", return_value=pro):
        with patch("ui.kicad_host.prepare_kicad_ui_launch", return_value=(True, parent)):
            with patch("plugin.assistant_window.show_assistant_window") as show_mock:
                plugin.Run()
                show_mock.assert_called_once_with(parent, pro)

    parent.Destroy()
