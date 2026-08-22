"""Conversation Manager — in-session multi-turn chat history (platform layer)."""

from conversation.session import ChatRole, ChatSession, ChatTurn
from conversation.store import SessionStore, conversation_file_path, get_session_store

__all__ = [
    "ChatRole",
    "ChatSession",
    "ChatTurn",
    "SessionStore",
    "conversation_file_path",
    "get_session_store",
]
