"""Provider and model settings dialog for the Assistant shell."""

from __future__ import annotations

from dataclasses import replace

from utils.config import AppConfig, load_config, save_config

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]


class SettingsDialog:
    """Edit AI provider profile and persist to ``~/kicad_ai_config.json``."""

    def __init__(self, parent: wx.Window | None, config: AppConfig | None = None) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for SettingsDialog")
        self._initial = config or load_config()
        self._saved: AppConfig | None = None

        self._dialog = wx.Dialog(
            parent,
            title="KiCad AI Settings",
            size=(520, 380),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        panel = wx.Panel(self._dialog)
        vbox = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(
            panel,
            label="Provider profile — saved to ~/kicad_ai_config.json and used by Chat and AERF.",
        )
        intro.Wrap(480)
        vbox.Add(intro, flag=wx.ALL, border=10)

        grid = wx.FlexGridSizer(0, 2, 8, 8)
        grid.AddGrowableCol(1, 1)

        grid.Add(wx.StaticText(panel, label="Provider:"), flag=wx.ALIGN_CENTER_VERTICAL)
        self._provider = wx.Choice(panel, choices=["claude", "ollama"])
        provider_idx = 0 if self._initial.ai_provider == "claude" else 1
        self._provider.SetSelection(provider_idx)
        grid.Add(self._provider, flag=wx.EXPAND)

        grid.Add(wx.StaticText(panel, label="Anthropic API key:"), flag=wx.ALIGN_CENTER_VERTICAL)
        self._anthropic_key = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        if self._initial.anthropic_api_key:
            self._anthropic_key.SetValue(self._initial.anthropic_api_key)
        grid.Add(self._anthropic_key, flag=wx.EXPAND)

        grid.Add(wx.StaticText(panel, label="Claude model:"), flag=wx.ALIGN_CENTER_VERTICAL)
        self._claude_model = wx.TextCtrl(panel)
        self._claude_model.SetValue(self._initial.claude_model)
        grid.Add(self._claude_model, flag=wx.EXPAND)

        grid.Add(wx.StaticText(panel, label="Ollama base URL:"), flag=wx.ALIGN_CENTER_VERTICAL)
        self._ollama_url = wx.TextCtrl(panel)
        self._ollama_url.SetValue(self._initial.ollama_base_url)
        grid.Add(self._ollama_url, flag=wx.EXPAND)

        grid.Add(wx.StaticText(panel, label="Ollama model:"), flag=wx.ALIGN_CENTER_VERTICAL)
        self._ollama_model = wx.TextCtrl(panel)
        self._ollama_model.SetValue(self._initial.ollama_model)
        grid.Add(self._ollama_model, flag=wx.EXPAND)

        vbox.Add(grid, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        btn_row.AddStretchSpacer()
        self._btn_save = wx.Button(panel, wx.ID_OK, label="Save")
        self._btn_cancel = wx.Button(panel, wx.ID_CANCEL, label="Cancel")
        btn_row.Add(self._btn_save, flag=wx.RIGHT, border=6)
        btn_row.Add(self._btn_cancel)
        vbox.Add(btn_row, flag=wx.EXPAND | wx.ALL, border=10)

        panel.SetSizer(vbox)
        self._btn_save.Bind(wx.EVT_BUTTON, self._on_save)
        self._btn_cancel.Bind(wx.EVT_BUTTON, self._on_cancel)

    @property
    def saved_config(self) -> AppConfig | None:
        return self._saved

    def show_modal(self) -> int:
        return self._dialog.ShowModal()

    def _on_cancel(self, _event: wx.CommandEvent) -> None:
        self._dialog.EndModal(wx.ID_CANCEL)

    def _on_save(self, _event: wx.CommandEvent) -> None:
        provider = self._provider.GetStringSelection().strip() or "claude"
        updated = replace(
            self._initial,
            ai_provider="ollama" if provider == "ollama" else "claude",
            anthropic_api_key=self._anthropic_key.GetValue().strip() or None,
            claude_model=self._claude_model.GetValue().strip() or self._initial.claude_model,
            ollama_base_url=self._ollama_url.GetValue().strip() or self._initial.ollama_base_url,
            ollama_model=self._ollama_model.GetValue().strip() or self._initial.ollama_model,
        )
        save_config(updated)
        self._saved = updated
        self._dialog.EndModal(wx.ID_OK)


def show_settings_dialog(
    parent: wx.Window | None = None,
    *,
    config: AppConfig | None = None,
) -> AppConfig | None:
    """Show settings dialog; return saved config or None if cancelled."""
    if wx is None:
        raise RuntimeError("wxPython is required for SettingsDialog")
    dlg = SettingsDialog(parent, config=config)
    if dlg.show_modal() == wx.ID_OK:
        return dlg.saved_config
    return None
