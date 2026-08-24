"""Side-by-side routing candidate comparison dialog."""

from __future__ import annotations

from typing import Any

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


def show_routing_comparison_dialog(
    parent: wx.Window,
    comparison: dict[str, Any],
) -> None:
    """Show a modal table of routing candidate metrics."""
    if wx is None:
        raise RuntimeError("wxPython is required for routing comparison dialog")

    headers: list[str] = list(comparison.get("columns") or [])
    rows: list[list[str]] = list(comparison.get("table") or [])
    summary = str(comparison.get("summary") or "")

    dialog = wx.Dialog(parent, title="Routing candidate comparison", size=(820, 360))
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(
        wx.StaticText(dialog, label=summary),
        flag=wx.ALL | wx.EXPAND,
        border=10,
    )

    list_ctrl = wx.ListCtrl(dialog, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
    for index, header in enumerate(headers):
        width = 220 if index == 0 else 110 if index < 4 else 260
        list_ctrl.InsertColumn(index, header, width=width)
    for row_index, row in enumerate(rows):
        list_ctrl.InsertItem(row_index, row[0] if row else "")
        for col_index, cell in enumerate(row[1:], start=1):
            list_ctrl.SetItem(row_index, col_index, cell)

    sizer.Add(list_ctrl, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
    btn_close = wx.Button(dialog, wx.ID_CLOSE, label="Close")
    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    btn_sizer.AddStretchSpacer()
    btn_sizer.Add(btn_close)
    sizer.Add(btn_sizer, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
    dialog.SetSizer(sizer)
    btn_close.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_OK))
    dialog.ShowModal()
    dialog.Destroy()
