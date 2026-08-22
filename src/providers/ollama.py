"""Ollama local LLM provider."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Callable

from providers.errors import (
    MalformedResponseError,
    ProviderError,
    TimeoutError as ProviderTimeoutError,
)
from providers.types import ProviderResponse, TokenUsage
from utils.config import AppConfig, load_config

HttpOpener = Callable[[urllib.request.Request, float], Any]


class OllamaProvider:
    """Ollama chat API provider (local or remote Ollama server)."""

    def __init__(
        self,
        config: AppConfig | None = None,
        *,
        opener: HttpOpener | None = None,
    ) -> None:
        self._config = config or load_config()
        self._opener = opener or urllib.request.urlopen

    def send_message(
        self,
        prompt: str,
        *,
        system: str | None = None,
        image: bytes | None = None,
        image_media_type: str = "image/png",
        config: AppConfig | None = None,
    ) -> ProviderResponse:
        if image is not None:
            raise ProviderError("Ollama provider does not support schematic images in this release.")
        return self.send_messages(
            [{"role": "user", "content": prompt}],
            system=system,
            config=config,
        )

    def send_messages(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        config: AppConfig | None = None,
    ) -> ProviderResponse:
        cfg = config or self._config
        base = (cfg.ollama_base_url or "").rstrip("/")
        if not base:
            raise ProviderError("Ollama base URL not configured.")

        payload: dict[str, Any] = {
            "model": cfg.ollama_model,
            "messages": self._build_messages(messages, system=system),
            "stream": False,
        }
        url = f"{base}/api/chat"
        raw = self._post_json(
            url,
            payload,
            connect_timeout_sec=min(30, cfg.provider_timeout_sec),
            read_timeout_sec=cfg.provider_read_timeout_sec,
        )
        return self._parse_response(raw, model=cfg.ollama_model)

    def _build_messages(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str | None,
    ) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        if system:
            out.append({"role": "system", "content": system})
        for msg in messages:
            role = str(msg.get("role", "user"))
            content = msg.get("content")
            if isinstance(content, str):
                out.append({"role": role, "content": content})
        return out

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        connect_timeout_sec: float,
        read_timeout_sec: float,
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(request, connect_timeout_sec + read_timeout_sec) as resp:
                body = resp.read().decode("utf-8")
        except socket.timeout as exc:
            raise ProviderTimeoutError(f"Ollama request timed out: {exc}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise MalformedResponseError(f"Invalid JSON from Ollama: {exc}") from exc
        if not isinstance(parsed, dict):
            raise MalformedResponseError("Ollama response was not a JSON object.")
        return parsed

    def _parse_response(self, raw: dict[str, Any], *, model: str) -> ProviderResponse:
        message = raw.get("message")
        if not isinstance(message, dict):
            raise MalformedResponseError("Ollama response missing message object.")
        text = message.get("content")
        if not isinstance(text, str):
            raise MalformedResponseError("Ollama response missing message content.")

        usage_raw = raw.get("eval_count")
        prompt_raw = raw.get("prompt_eval_count")
        usage = TokenUsage(
            input_tokens=int(prompt_raw) if isinstance(prompt_raw, int) else 0,
            output_tokens=int(usage_raw) if isinstance(usage_raw, int) else 0,
        )
        return ProviderResponse(
            text=text,
            model=str(raw.get("model", model)),
            usage=usage,
            stop_reason=str(raw.get("done_reason")) if raw.get("done_reason") else None,
            raw=raw,
        )
