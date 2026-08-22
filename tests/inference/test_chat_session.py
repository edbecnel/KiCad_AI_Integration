"""Tests for multi-turn chat inference."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from context.context_cache import save_context_cache
from context.context_flags import ContextIncludeFlags
from context.model import ProjectContext
from conversation.session import ChatSession
from inference.chat import build_followup_prompt, prepare_followup_context, send_chat_prompt
from prompts import BuiltPrompt
from providers.types import ProviderResponse, TokenUsage


def _ctx() -> ProjectContext:
    return ProjectContext(
        project_path="/tmp/test.kicad_pro",
        project_name="test",
        symbols=[],
        netlist_summary={"status_line": "SPICE netlist: 10 lines"},
    )


def test_build_followup_prompt_is_lighter_than_first_turn() -> None:
    ctx = _ctx()
    first = build_followup_prompt(ctx, "What is U3?", template="general_review")
    assert "Follow-up question" in first.text
    assert "test" in first.text
    assert first.include_image is False
    assert first.system is not None


def test_build_followup_prompt_uses_cache_when_provided(tmp_path: Path) -> None:
    pro = tmp_path / "test.kicad_pro"
    sch = tmp_path / "test.kicad_sch"
    pro.write_text("{}", encoding="utf-8")
    sch.write_text("sch", encoding="utf-8")

    ctx = ProjectContext(
        project_path=str(pro),
        project_name="test",
        symbols=[],
        netlist_summary={"status_line": "SPICE netlist: 10 lines"},
    )
    entry = save_context_cache(pro, ctx)
    built = build_followup_prompt(
        ctx,
        "What is U3?",
        template="general_review",
        project_path=pro,
        dirty_layers=set(),
        cache_entry=entry,
    )
    assert "Cached project snapshot" in built.text
    assert "Follow-up question" in built.text


def test_prepare_followup_context_refreshes_dirty_layers(tmp_path: Path) -> None:
    pro = tmp_path / "test.kicad_pro"
    sch = tmp_path / "test.kicad_sch"
    pro.write_text("{}", encoding="utf-8")
    sch.write_text("v1", encoding="utf-8")

    from context.fingerprint import compute_fingerprint, save_fingerprint

    save_fingerprint(compute_fingerprint(pro))
    sch.write_text("v2", encoding="utf-8")

    ctx = ProjectContext(project_path=str(pro), project_name="test", symbols=[])
    updated, dirty, _cache = prepare_followup_context(
        ctx,
        pro,
        include_flags=ContextIncludeFlags(schematic=True),
    )
    assert "schematic" in dirty
    assert updated is not None


def test_send_chat_prompt_uses_send_messages_on_followup() -> None:
    ctx = _ctx()
    session = ChatSession(project_path=Path(ctx.project_path))
    session.append_user("first", api_content="full context prompt")
    session.append_assistant("first answer")

    provider = MagicMock()
    provider.send_messages.return_value = ProviderResponse(
        text="follow-up answer",
        model="claude-test",
        usage=TokenUsage(input_tokens=3, output_tokens=4),
    )
    built = BuiltPrompt(
        text="follow-up body",
        system="system prompt",
        template="general_review",
        preview_summary="follow-up",
        estimated_text_tokens=10,
    )

    result = send_chat_prompt(built, ctx, provider=provider, session=session)

    provider.send_message.assert_not_called()
    provider.send_messages.assert_called_once()
    messages = provider.send_messages.call_args.args[0]
    assert messages[-1] == {"role": "user", "content": "follow-up body"}
    assert result.response.text == "follow-up answer"


def test_send_chat_prompt_uses_send_message_on_first_turn() -> None:
    ctx = _ctx()
    provider = MagicMock()
    provider.send_message.return_value = ProviderResponse(
        text="answer",
        model="claude-test",
        usage=TokenUsage(input_tokens=1, output_tokens=2),
    )
    built = BuiltPrompt(
        text="first prompt",
        system="system",
        template="general_review",
        preview_summary="first",
        estimated_text_tokens=20,
        include_image=False,
    )

    send_chat_prompt(built, ctx, provider=provider)

    provider.send_messages.assert_not_called()
    provider.send_message.assert_called_once()
