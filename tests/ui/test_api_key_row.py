"""Tests for shared API key row show/hide toggle."""

from __future__ import annotations

import pytest

_wx_app: object | None = None


def _ensure_wx_app():
    pytest.importorskip("wx")
    import wx

    global _wx_app
    if wx.GetApp() is None:
        try:
            _wx_app = wx.App(False)
        except SystemExit:
            pytest.skip("wx display not available")
    return wx


def _toggle_show(row, *, show: bool) -> None:
    import wx

    row.show_checkbox.SetValue(show)
    event = wx.CommandEvent(wx.EVT_CHECKBOX.typeId, row.show_checkbox.GetId())
    event.SetInt(1 if show else 0)
    row.show_checkbox.GetEventHandler().ProcessEvent(event)


def test_api_key_row_masks_by_default() -> None:
    wx = _ensure_wx_app()
    from ui.api_key_row import ApiKeyRow

    frame = wx.Frame(None, title="test")
    row = ApiKeyRow.create(frame, initial_value="sk-ant-test-key")
    frame.Show(False)

    assert row.get_value() == "sk-ant-test-key"
    assert row.text is row._masked
    assert row.text.GetWindowStyleFlag() & wx.TE_PASSWORD
    assert not row.show_checkbox.GetValue()
    assert not row._hint.IsShown()

    frame.Destroy()


def test_api_key_row_show_reveals_plain_text_control() -> None:
    wx = _ensure_wx_app()
    from ui.api_key_row import ApiKeyRow

    frame = wx.Frame(None, title="test")
    row = ApiKeyRow.create(frame, initial_value="sk-ant-visible")
    frame.Show(False)

    _toggle_show(row, show=True)

    assert row.get_value() == "sk-ant-visible"
    assert row.text is row._plain
    assert not (row.text.GetWindowStyleFlag() & wx.TE_PASSWORD)
    assert row._plain.IsShown()
    assert not row._masked.IsShown()

    _toggle_show(row, show=False)

    assert row.get_value() == "sk-ant-visible"
    assert row.text is row._masked
    assert row._masked.IsShown()
    assert not row._plain.IsShown()

    frame.Destroy()


def test_api_key_row_shows_hint_when_empty() -> None:
    wx = _ensure_wx_app()
    from ui.api_key_row import ApiKeyRow

    frame = wx.Frame(None, title="test")
    row = ApiKeyRow.create(frame)
    frame.Show(False)

    assert row.get_value() == ""
    assert row._hint.IsShown()
    assert "Settings" in row._hint.GetLabel()

    row.set_value("sk-ant-set")
    assert not row._hint.IsShown()

    frame.Destroy()
