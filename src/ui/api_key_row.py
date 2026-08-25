"""Shared API key entry row with show/hide toggle."""

from __future__ import annotations

from dataclasses import dataclass, field

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]

_EMPTY_KEY_HINT = (
    "Not set — paste sk-ant-… here, or use Settings… → Save to load from ~/kicad_ai_config.json"
)


@dataclass
class ApiKeyRow:
    """Label, masked/plain text controls, Show checkbox, and empty-key hint."""

    sizer: wx.BoxSizer
    _masked: wx.TextCtrl = field(repr=False)
    _plain: wx.TextCtrl = field(repr=False)
    show_checkbox: wx.CheckBox = field(repr=False)
    _hint: wx.StaticText = field(repr=False)
    _show_plain: bool = field(default=False, repr=False)

    @property
    def text(self) -> wx.TextCtrl:
        """Visible text control (for tests and focus)."""
        return self._plain if self._show_plain else self._masked

    @classmethod
    def create(
        cls,
        parent: wx.Window,
        *,
        initial_value: str | None = None,
        label: str = "API key:",
    ) -> ApiKeyRow:
        if wx is None:
            raise RuntimeError("wxPython is required for ApiKeyRow")

        outer = wx.BoxSizer(wx.VERTICAL)
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(parent, label=label), flag=wx.RIGHT, border=6)

        text_slot = wx.BoxSizer(wx.HORIZONTAL)
        masked = wx.TextCtrl(parent, style=wx.TE_PASSWORD)
        plain = wx.TextCtrl(parent)
        text_slot.Add(masked, proportion=1, flag=wx.EXPAND)
        text_slot.Add(plain, proportion=1, flag=wx.EXPAND)
        plain.Hide()
        row.Add(text_slot, proportion=1, flag=wx.EXPAND)

        show_checkbox = wx.CheckBox(parent, label="Show")
        row.Add(show_checkbox, flag=wx.LEFT, border=8)
        outer.Add(row, flag=wx.EXPAND)

        hint = wx.StaticText(parent, label=_EMPTY_KEY_HINT)
        hint.Wrap(760)
        hint.SetForegroundColour(wx.Colour(120, 120, 120))
        outer.Add(hint, flag=wx.TOP, border=4)

        instance = cls(
            sizer=outer,
            _masked=masked,
            _plain=plain,
            show_checkbox=show_checkbox,
            _hint=hint,
        )

        for ctrl in (masked, plain):
            ctrl.SetHint(_EMPTY_KEY_HINT)
            ctrl.Bind(wx.EVT_TEXT, instance._on_text_changed)

        if initial_value:
            instance.set_value(initial_value)

        show_checkbox.Bind(wx.EVT_CHECKBOX, instance._on_toggle_show)
        instance._sync_hint_visibility()
        return instance

    def get_value(self) -> str:
        """Return the current API key (masked and plain controls stay in sync)."""
        return self.text.GetValue()

    def set_value(self, value: str) -> None:
        self._masked.SetValue(value)
        self._plain.SetValue(value)
        self._sync_hint_visibility()

    def _on_text_changed(self, _event: wx.CommandEvent) -> None:
        if self._show_plain:
            self._masked.SetValue(self._plain.GetValue())
        else:
            self._plain.SetValue(self._masked.GetValue())
        self._sync_hint_visibility()

    def _sync_hint_visibility(self) -> None:
        empty = not self.get_value().strip()
        if self._hint.IsShown() != empty:
            self._hint.Show(empty)
            self._hint.GetParent().Layout()

    def _on_toggle_show(self, event: wx.CommandEvent) -> None:
        show_plain = event.IsChecked()
        if show_plain:
            self._plain.SetValue(self._masked.GetValue())
            self._masked.Hide()
            self._plain.Show()
        else:
            self._masked.SetValue(self._plain.GetValue())
            self._plain.Hide()
            self._masked.Show()
        self._show_plain = show_plain
        self.text.GetParent().Layout()
        self._sync_hint_visibility()
