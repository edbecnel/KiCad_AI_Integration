"""Notebook renderer — wx widgets for EKM sections and fields (ADP-003)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ekm.errors import EKMError
from ekm.view_model import EKMViewModel, FieldView, SectionView, reference_kind_choices

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]

OnChangeCallback = Callable[[], None]


class CollapsibleSection(wx.Panel):
    """Expandable section container with a toggle header."""

    def __init__(
        self,
        parent: wx.Window,
        section: SectionView,
        *,
        vm: EKMViewModel,
        on_change: OnChangeCallback,
        on_status: Callable[[str], None],
        initially_expanded: bool = True,
    ) -> None:
        super().__init__(parent)
        self._section = section
        self._vm = vm
        self._on_change = on_change
        self._on_status = on_status
        self._expanded = initially_expanded

        root = wx.BoxSizer(wx.VERTICAL)
        header_row = wx.BoxSizer(wx.HORIZONTAL)
        self._toggle = wx.Button(self, label="▼" if initially_expanded else "▶", size=(28, -1))
        self._title = wx.StaticText(self, label=section.title)
        header_row.Add(self._toggle, flag=wx.RIGHT, border=4)
        header_row.Add(self._title, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        root.Add(header_row, flag=wx.EXPAND | wx.ALL, border=4)

        self._body = wx.Panel(self)
        body_sizer = wx.BoxSizer(wx.VERTICAL)
        meta = wx.StaticText(self._body, label=f"Section id: {section.section_id}")
        body_sizer.Add(meta, flag=wx.ALL, border=4)
        if not section.fields:
            body_sizer.Add(
                wx.StaticText(self._body, label="(no fields)"),
                flag=wx.LEFT | wx.RIGHT | wx.BOTTOM,
                border=4,
            )
        for field in section.fields:
            body_sizer.Add(
                build_field_panel(self._body, field, vm=vm, on_change=on_change, on_status=on_status),
                flag=wx.EXPAND | wx.ALL,
                border=4,
            )
        self._body.SetSizer(body_sizer)
        root.Add(self._body, flag=wx.EXPAND)
        self.SetSizer(root)
        self._apply_expanded()

        self._toggle.Bind(wx.EVT_BUTTON, self._on_toggle)
        self._title.Bind(wx.EVT_LEFT_DOWN, self._on_toggle)

    def section_id(self) -> str:
        return self._section.section_id

    def _on_toggle(self, _event: wx.Event) -> None:
        self._expanded = not self._expanded
        self._apply_expanded()

    def _apply_expanded(self) -> None:
        self._body.Show(self._expanded)
        self._toggle.SetLabel("▼" if self._expanded else "▶")
        self.Layout()


def build_field_panel(
    parent: wx.Window,
    field: FieldView,
    *,
    vm: EKMViewModel,
    on_change: OnChangeCallback,
    on_status: Callable[[str], None],
) -> wx.Window:
    row = wx.BoxSizer(wx.VERTICAL)
    row.Add(wx.StaticText(parent, label=field.label), flag=wx.BOTTOM, border=2)

    if field.editor_kind == "text":
        editor = wx.TextCtrl(parent, value=str(field.value or ""), style=wx.TE_MULTILINE)
        editor.SetMinSize((-1, 72))
        editor.Bind(
            wx.EVT_TEXT,
            lambda _e, s=field.section_id, f=field.field_id, ctrl=editor: _apply_text(
                vm, s, f, ctrl, on_change, on_status
            ),
        )
    elif field.editor_kind == "enum":
        editor = wx.Choice(parent, choices=field.options)
        if field.value in field.options:
            editor.SetStringSelection(str(field.value))
        editor.Bind(
            wx.EVT_CHOICE,
            lambda _e, s=field.section_id, f=field.field_id, ctrl=editor: _apply_enum(
                vm, s, f, ctrl, on_change, on_status
            ),
        )
    elif field.editor_kind == "number":
        editor = wx.BoxSizer(wx.HORIZONTAL)
        value_ctrl = wx.TextCtrl(parent, value=str(field.value if field.value is not None else ""))
        unit = field.raw.get("unit")
        unit_label = wx.StaticText(parent, label=str(unit) if unit else "")
        editor.Add(value_ctrl, proportion=1, flag=wx.RIGHT, border=4)
        editor.Add(unit_label, flag=wx.ALIGN_CENTER_VERTICAL)
        value_ctrl.Bind(
            wx.EVT_TEXT,
            lambda _e, s=field.section_id, f=field.field_id, ctrl=value_ctrl: _apply_number(
                vm, s, f, ctrl, on_change, on_status
            ),
        )
        panel = wx.Panel(parent)
        panel.SetSizer(editor)
        return panel
    elif field.editor_kind == "measurement":
        editor = wx.BoxSizer(wx.VERTICAL)
        value_row = wx.BoxSizer(wx.HORIZONTAL)
        meas = field.value if isinstance(field.value, dict) else {}
        value_ctrl = wx.TextCtrl(parent, value=str(meas.get("value", "")))
        unit_ctrl = wx.TextCtrl(parent, value=str(meas.get("unit", "")))
        value_row.Add(wx.StaticText(parent, label="Value:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
        value_row.Add(value_ctrl, proportion=1, flag=wx.RIGHT, border=4)
        value_row.Add(wx.StaticText(parent, label="Unit:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
        value_row.Add(unit_ctrl, proportion=1)
        conditions_ctrl = wx.TextCtrl(parent, value=str(meas.get("conditions", "")))
        editor.Add(value_row, flag=wx.EXPAND | wx.BOTTOM, border=4)
        editor.Add(wx.StaticText(parent, label="Conditions:"), flag=wx.BOTTOM, border=2)
        editor.Add(conditions_ctrl, flag=wx.EXPAND)

        def _bind_measurement(_event: wx.Event) -> None:
            _apply_measurement(
                vm,
                field.section_id,
                field.field_id,
                value_ctrl,
                unit_ctrl,
                conditions_ctrl,
                on_change,
                on_status,
            )

        value_ctrl.Bind(wx.EVT_TEXT, _bind_measurement)
        unit_ctrl.Bind(wx.EVT_TEXT, _bind_measurement)
        conditions_ctrl.Bind(wx.EVT_TEXT, _bind_measurement)
        panel = wx.Panel(parent)
        panel.SetSizer(editor)
        return panel
    elif field.editor_kind == "reference":
        editor = wx.BoxSizer(wx.VERTICAL)
        ref = field.value if isinstance(field.value, dict) else {}
        kind_row = wx.BoxSizer(wx.HORIZONTAL)
        kind_row.Add(wx.StaticText(parent, label="Kind:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
        kind_ctrl = wx.Choice(parent, choices=reference_kind_choices())
        if ref.get("kind") in reference_kind_choices():
            kind_ctrl.SetStringSelection(str(ref.get("kind")))
        kind_row.Add(kind_ctrl, proportion=1)
        ref_row = wx.BoxSizer(wx.HORIZONTAL)
        ref_row.Add(wx.StaticText(parent, label="Ref:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
        ref_ctrl = wx.TextCtrl(parent, value=str(ref.get("ref", "")))
        ref_row.Add(ref_ctrl, proportion=1)
        sheet_row = wx.BoxSizer(wx.HORIZONTAL)
        sheet_row.Add(
            wx.StaticText(parent, label="Sheet path:"),
            flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
            border=4,
        )
        sheet_ctrl = wx.TextCtrl(parent, value=str(ref.get("sheet_path", "")))
        sheet_row.Add(sheet_ctrl, proportion=1)
        editor.Add(kind_row, flag=wx.EXPAND | wx.BOTTOM, border=4)
        editor.Add(ref_row, flag=wx.EXPAND | wx.BOTTOM, border=4)
        editor.Add(sheet_row, flag=wx.EXPAND)

        def _bind_reference(_event: wx.Event) -> None:
            _apply_reference(
                vm,
                field.section_id,
                field.field_id,
                kind_ctrl,
                ref_ctrl,
                sheet_ctrl,
                on_change,
                on_status,
            )

        kind_ctrl.Bind(wx.EVT_CHOICE, _bind_reference)
        ref_ctrl.Bind(wx.EVT_TEXT, _bind_reference)
        sheet_ctrl.Bind(wx.EVT_TEXT, _bind_reference)
        panel = wx.Panel(parent)
        panel.SetSizer(editor)
        return panel
    else:
        editor = wx.TextCtrl(
            parent,
            value=field.display_value or str(field.value),
            style=wx.TE_MULTILINE | wx.TE_READONLY,
        )
        editor.SetMinSize((-1, 48))

    row.Add(editor, proportion=0, flag=wx.EXPAND)
    panel = wx.Panel(parent)
    panel.SetSizer(row)
    return panel


def build_sections_container(
    parent: wx.Window,
    sections: list[SectionView],
    *,
    vm: EKMViewModel,
    on_change: OnChangeCallback,
    on_status: Callable[[str], None],
) -> tuple[wx.BoxSizer, list[CollapsibleSection]]:
    container = wx.BoxSizer(wx.VERTICAL)
    widgets: list[CollapsibleSection] = []
    for section in sections:
        widget = CollapsibleSection(
            parent,
            section,
            vm=vm,
            on_change=on_change,
            on_status=on_status,
        )
        widgets.append(widget)
        container.Add(widget, flag=wx.EXPAND | wx.ALL, border=6)
    return container, widgets


def _apply_text(
    vm: EKMViewModel,
    section_id: str,
    field_id: str,
    ctrl: wx.TextCtrl,
    on_change: OnChangeCallback,
    on_status: Callable[[str], None],
) -> None:
    try:
        vm.update_text_field(section_id, field_id, ctrl.GetValue())
    except EKMError as exc:
        on_status(str(exc))
        return
    on_change()


def _apply_enum(
    vm: EKMViewModel,
    section_id: str,
    field_id: str,
    ctrl: wx.Choice,
    on_change: OnChangeCallback,
    on_status: Callable[[str], None],
) -> None:
    try:
        vm.update_enum_field(section_id, field_id, ctrl.GetStringSelection())
    except EKMError as exc:
        on_status(str(exc))
        return
    on_change()


def _apply_number(
    vm: EKMViewModel,
    section_id: str,
    field_id: str,
    ctrl: wx.TextCtrl,
    on_change: OnChangeCallback,
    on_status: Callable[[str], None],
) -> None:
    try:
        from ekm.field_registry import parse_number_input

        vm.update_number_field(section_id, field_id, parse_number_input(ctrl.GetValue()))
    except (EKMError, ValueError) as exc:
        on_status(str(exc))
        return
    on_change()


def _apply_measurement(
    vm: EKMViewModel,
    section_id: str,
    field_id: str,
    value_ctrl: wx.TextCtrl,
    unit_ctrl: wx.TextCtrl,
    conditions_ctrl: wx.TextCtrl,
    on_change: OnChangeCallback,
    on_status: Callable[[str], None],
) -> None:
    try:
        from ekm.field_registry import parse_measurement_input

        payload = parse_measurement_input(
            value_ctrl.GetValue(),
            unit_ctrl.GetValue(),
            conditions_ctrl.GetValue(),
        )
        vm.update_measurement_field(
            section_id,
            field_id,
            float(payload["value"]),
            str(payload["unit"]),
            conditions=str(payload.get("conditions") or ""),
        )
    except (EKMError, ValueError) as exc:
        on_status(str(exc))
        return
    on_change()


def _apply_reference(
    vm: EKMViewModel,
    section_id: str,
    field_id: str,
    kind_ctrl: wx.Choice,
    ref_ctrl: wx.TextCtrl,
    sheet_ctrl: wx.TextCtrl,
    on_change: OnChangeCallback,
    on_status: Callable[[str], None],
) -> None:
    try:
        vm.update_reference_field(
            section_id,
            field_id,
            kind_ctrl.GetStringSelection(),
            ref_ctrl.GetValue(),
            sheet_path=sheet_ctrl.GetValue(),
        )
    except (EKMError, ValueError) as exc:
        on_status(str(exc))
        return
    on_change()
