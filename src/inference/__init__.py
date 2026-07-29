"""Engineering Inference Engine (EIE) — platform inference orchestration."""

from inference.chat import (
    ChatSendResult,
    build_chat_prompt,
    collect_chat_context,
    send_chat_prompt,
)

__all__ = [
    "ChatSendResult",
    "build_chat_prompt",
    "collect_chat_context",
    "send_chat_prompt",
]
