"""Tests for Assistant shell foundation (ADP-011 Phase A)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ui.assistant_tab import ASSISTANT_TAB_IDS, tab_index_for_focus
from ui.context_controller import ContextController
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
_wx_app: object | None = None


def _ensure_wx_app():
    import wx

    global _wx_app
    if wx.GetApp() is None:
        _wx_app = wx.App(False)
    return wx


@pytest.fixture
def test_config(tmp_path: Path) -> AppConfig:
    return AppConfig(artifact_library_path=tmp_path / "library")


def test_tab_index_for_focus_known_tab() -> None:
    assert tab_index_for_focus("notebook") == ASSISTANT_TAB_IDS.index("notebook")
    assert tab_index_for_focus("chat") == 0


def test_tab_index_for_focus_unknown_or_empty() -> None:
    assert tab_index_for_focus(None) is None
    assert tab_index_for_focus("unknown") is None


def test_context_controller_refresh_populates_context_and_summary(test_config: AppConfig) -> None:
    pro = FIXTURES / "testproj.kicad_pro"
    controller = ContextController(config=test_config)
    seen: list[tuple[str, str]] = []

    def listener(ctx, summary: str) -> None:
        seen.append((ctx.project_name, summary))

    controller.bind_listener(listener)
    controller.refresh(pro)

    assert controller.last_error is None
    assert controller.project_path == pro.resolve()
    assert controller.context is not None
    assert controller.context.project_name
    assert controller.summary_text
    assert len(seen) == 1
    assert seen[0][0] == controller.context.project_name
    assert seen[0][1] == controller.summary_text


def test_context_controller_refresh_notifies_multiple_listeners(test_config: AppConfig) -> None:
    pro = FIXTURES / "testproj.kicad_pro"
    controller = ContextController(config=test_config)
    counts = {"a": 0, "b": 0}

    controller.bind_listener(lambda _ctx, _summary: counts.__setitem__("a", counts["a"] + 1))
    controller.bind_listener(lambda _ctx, _summary: counts.__setitem__("b", counts["b"] + 1))
    controller.refresh(pro)

    assert counts == {"a": 1, "b": 1}


def test_context_controller_refresh_missing_project_sets_error(test_config: AppConfig) -> None:
    controller = ContextController(config=test_config)
    controller.refresh(Path("/nonexistent/project.kicad_pro"))

    assert controller.last_error is not None
    assert controller.context is None
    assert controller.summary_text == ""


def test_assistant_shell_notebook_tab_embedded_after_refresh() -> None:
    pytest.importorskip("wx")
    wx = _ensure_wx_app()

    from ui.assistant_shell import AssistantShell

    frame = wx.Frame(None, title="test")
    shell = AssistantShell(frame, initial_path=FIXTURES / "testproj.kicad_pro", focus_tab="notebook")
    frame.Show(False)

    idx = shell._notebook.GetSelection()
    assert ASSISTANT_TAB_IDS[idx] == "notebook"

    page = shell._notebook.GetPage(idx)
    assert shell._notebook_tab is not None
    assert page is shell._notebook_tab
    assert shell._notebook_tab._shell is not None

    frame.Destroy()


def test_assistant_shell_focus_tab_selects_page() -> None:
    pytest.importorskip("wx")
    wx = _ensure_wx_app()

    from ui.assistant_shell import AssistantShell

    frame = wx.Frame(None, title="test")
    shell = AssistantShell(frame, focus_tab="simulation")
    assert shell._notebook.GetSelection() == ASSISTANT_TAB_IDS.index("simulation")
    frame.Destroy()


@pytest.mark.parametrize(
    "focus_tab",
    ("chat", "datasheets", "simulation", "aerf", "notebook", "audits", "routing"),
)
def test_assistant_shell_cli_deep_links_select_tab(focus_tab: str) -> None:
    pytest.importorskip("wx")
    wx = _ensure_wx_app()

    from ui.assistant_shell import AssistantShell

    pro = FIXTURES / "testproj.kicad_pro"
    frame = wx.Frame(None, title="test")
    shell = AssistantShell(frame, initial_path=pro, focus_tab=focus_tab)
    frame.Show(False)

    assert shell._notebook.GetSelection() == ASSISTANT_TAB_IDS.index(focus_tab)
    frame.Destroy()


def test_assistant_shell_context_propagates_to_all_tabs(test_config: AppConfig) -> None:
    pytest.importorskip("wx")
    wx = _ensure_wx_app()

    from ui.assistant_shell import AssistantShell

    pro = FIXTURES / "testproj.kicad_pro"
    frame = wx.Frame(None, title="test")
    shell = AssistantShell(frame, initial_path=pro)
    frame.Show(False)

    assert shell._controller.context is not None
    for tab_id in ASSISTANT_TAB_IDS:
        tab = shell._tabs[tab_id]
        assert not tab._placeholder.IsShown(), f"{tab_id} still showing placeholder"
        if tab_id == "notebook":
            assert shell._notebook_tab is not None
            assert shell._notebook_tab._shell is not None
        else:
            assert tab._shell is not None

    frame.Destroy()


def test_assistant_shell_datasheets_tab_badge_after_refresh(test_config: AppConfig) -> None:
    pytest.importorskip("wx")
    wx = _ensure_wx_app()

    from ui.assistant_shell import AssistantShell

    pro = FIXTURES / "testproj.kicad_pro"
    frame = wx.Frame(None, title="test")
    shell = AssistantShell(frame, initial_path=pro)
    frame.Show(False)

    idx = ASSISTANT_TAB_IDS.index("datasheets")
    label = shell._notebook.GetPageText(idx)
    assert label.startswith("Datasheets")

    frame.Destroy()


def test_assistant_shell_restores_last_tab_per_project(
    test_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("wx")
    wx = _ensure_wx_app()

    from ui.assistant_shell import AssistantShell

    pro = FIXTURES / "testproj.kicad_pro"
    monkeypatch.setattr("ui.assistant_shell.get_last_tab", lambda _path: "aerf")

    frame = wx.Frame(None, title="test")
    shell = AssistantShell(frame, initial_path=pro)
    frame.Show(False)

    assert shell._notebook.GetSelection() == ASSISTANT_TAB_IDS.index("aerf")
    frame.Destroy()
