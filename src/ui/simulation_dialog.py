"""Modal wrapper for the embeddable simulation panel."""

from __future__ import annotations

from pathlib import Path

from ui.simulation_shell import SimulationShell

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


def show_simulation_dialog(
    project_path: Path | str,
    *,
    config=None,
    parent: object | None = None,
) -> None:
    """Open the Simulation models panel (modal)."""
    if wx is None:
        raise RuntimeError("wxPython is required")
    path = Path(project_path).expanduser().resolve()
    dlg = wx.Dialog(
        parent,
        title="Simulation models (SUBCKT)",
        size=(860, 560),
        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
    )
    shell = SimulationShell(dlg, path, embedded=False, config=config)
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(shell, proportion=1, flag=wx.EXPAND)
    dlg.SetSizer(sizer)
    dlg.ShowModal()
    dlg.Destroy()
