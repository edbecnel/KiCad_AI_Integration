"""Tests for macOS full-screen overlay detection (KiCad Scripting Console)."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch


def test_macos_fullscreen_overlay_blocked_on_linux() -> None:
    from ui.kicad_host import macos_fullscreen_overlay_blocked

    blocked, message = macos_fullscreen_overlay_blocked(object())
    assert blocked is False
    assert message == ""


def test_macos_fullscreen_overlay_blocked_when_not_embedded() -> None:
    from ui.kicad_host import macos_fullscreen_overlay_blocked

    with patch("ui.kicad_host.is_embedded_in_kicad", return_value=False):
        with patch.object(sys, "platform", "darwin"):
            blocked, message = macos_fullscreen_overlay_blocked(object())
    assert blocked is False
    assert message == ""


def test_macos_fullscreen_overlay_blocked_when_editor_fullscreen() -> None:
    from ui.kicad_host import macos_fullscreen_overlay_blocked

    editor = MagicMock()
    editor.IsFullScreen.return_value = True

    with patch("ui.kicad_host.is_embedded_in_kicad", return_value=True):
        with patch.object(sys, "platform", "darwin"):
            blocked, message = macos_fullscreen_overlay_blocked(editor)
    assert blocked is True
    assert "full-screen" in message.lower()
    assert "Control+Command+F" in message


def test_macos_fullscreen_overlay_blocked_when_editor_windowed() -> None:
    from ui.kicad_host import macos_fullscreen_overlay_blocked

    editor = MagicMock()
    editor.IsFullScreen.return_value = False

    with patch("ui.kicad_host.is_embedded_in_kicad", return_value=True):
        with patch.object(sys, "platform", "darwin"):
            blocked, message = macos_fullscreen_overlay_blocked(editor)
    assert blocked is False
    assert message == ""


def test_ensure_ui_can_display_or_warn_shows_message_and_returns_false() -> None:
    from ui.kicad_host import ensure_ui_can_display_or_warn

    wx_mod = types.ModuleType("wx")
    wx_mod.OK = 1
    wx_mod.ICON_INFORMATION = 64
    messages: list[tuple[str, str, int]] = []

    def message_box(caption: str, title: str, flags: int) -> int:
        messages.append((caption, title, flags))
        return wx_mod.OK

    wx_mod.MessageBox = message_box

    editor = MagicMock()
    editor.IsFullScreen.return_value = True

    with patch.object(sys, "platform", "darwin"):
        with patch("ui.kicad_host.is_embedded_in_kicad", return_value=True):
            with patch.dict(sys.modules, {"wx": wx_mod}):
                ok = ensure_ui_can_display_or_warn(editor)
    assert ok is False
    assert len(messages) == 1
    assert messages[0][1] == "KiCad AI Assistant"


def test_prepare_kicad_ui_launch_aborts_on_fullscreen() -> None:
    from ui.kicad_host import prepare_kicad_ui_launch

    editor = MagicMock()
    editor.IsFullScreen.return_value = True

    with patch("ui.launcher.ensure_wx_app"):
        with patch("ui.launcher.resolve_ui_parent", return_value=editor):
            with patch("ui.kicad_host.ensure_ui_can_display_or_warn", return_value=False):
                ok, parent = prepare_kicad_ui_launch(None)
    assert ok is False
    assert parent is None


def test_prepare_kicad_ui_launch_returns_parent_when_ok() -> None:
    from ui.kicad_host import prepare_kicad_ui_launch

    editor = object()
    with patch("ui.launcher.ensure_wx_app"):
        with patch("ui.launcher.resolve_ui_parent", return_value=editor):
            with patch("ui.kicad_host.ensure_ui_can_display_or_warn", return_value=True):
                ok, parent = prepare_kicad_ui_launch(None)
    assert ok is True
    assert parent is editor
