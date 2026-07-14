"""Anthropic Claude Messages API provider."""

from __future__ import annotations

import base64
import json
import socket
import urllib.error
import urllib.request
from typing import Any, Callable

from providers.errors import (
    AuthError,
    MalformedResponseError,
    ProviderError,
    RateLimitError,
    TimeoutError as ProviderTimeoutError,
)
from providers.types import ProviderResponse, TokenUsage
from utils.config import AppConfig, load_config

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

HttpOpener = Callable[[urllib.request.Request, float], Any]


class ClaudeProvider:
    """Claude Sonnet provider via Anthropic Messages API (stdlib HTTP)."""

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
        cfg = config or self._config
        api_key = (cfg.anthropic_api_key or "").strip()
        if not api_key:
            raise AuthError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY or "
                "anthropic_api_key in ~/kicad_ai_config.json."
            )

        payload = self._build_payload(
            prompt,
            system=system,
            image=image,
            image_media_type=image_media_type,
            config=cfg,
        )
        raw = self._post_json(payload, api_key=api_key, timeout_sec=cfg.provider_timeout_sec)
        return self._parse_response(raw, model=cfg.claude_model)

    def _build_payload(
        self,
        prompt: str,
        *,
        system: str | None,
        image: bytes | None,
        image_media_type: str,
        config: AppConfig,
    ) -> dict[str, Any]:
        if image is not None:
            content: str | list[dict[str, Any]] = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type,
                        "data": base64.b64encode(image).decode("ascii"),
                    },
                },
                {"type": "text", "text": prompt},
            ]
        else:
            content = prompt

        payload: dict[str, Any] = {
            "model": config.claude_model,
            "max_tokens": config.provider_max_tokens,
            "messages": [{"role": "user", "content": content}],
        }
        if system:
            payload["system"] = system
        return payload

    def _post_json(
        self,
        payload: dict[str, Any],
        *,
        api_key: str,
        timeout_sec: int,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            ANTHROPIC_MESSAGES_URL,
            data=body,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener(request, float(timeout_sec)) as response:
                raw_bytes = response.read()
        except urllib.error.HTTPError as exc:
            raise self._classify_http_error(exc) from exc
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, (TimeoutError, socket.timeout)):
                raise ProviderTimeoutError(
                    f"Anthropic API request timed out after {timeout_sec}s"
                ) from exc
            if "timed out" in str(reason).lower():
                raise ProviderTimeoutError(
                    f"Anthropic API request timed out after {timeout_sec}s"
                ) from exc
            raise ProviderError(f"Anthropic API request failed: {reason}") from exc
        except TimeoutError as exc:
            raise ProviderTimeoutError(
                f"Anthropic API request timed out after {timeout_sec}s"
            ) from exc

        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MalformedResponseError("Anthropic API returned non-JSON response") from exc

        if not isinstance(data, dict):
            raise MalformedResponseError("Anthropic API response must be a JSON object")
        return data

    def _classify_http_error(self, exc: urllib.error.HTTPError) -> ProviderError:
        status = exc.code
        detail = self._read_error_body(exc)
        message = detail or f"Anthropic API HTTP {status}"
        if status == 401:
            return AuthError(message, status_code=status)
        if status == 429:
            return RateLimitError(message, status_code=status)
        if status in (408, 504):
            return ProviderTimeoutError(message, status_code=status)
        return ProviderError(message, status_code=status)

    @staticmethod
    def _read_error_body(exc: urllib.error.HTTPError) -> str:
        try:
            raw = exc.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            if isinstance(data, dict):
                err = data.get("error")
                if isinstance(err, dict) and err.get("message"):
                    return str(err["message"])
                if data.get("message"):
                    return str(data["message"])
            return raw.strip()
        except Exception:
            return str(exc.reason)

    def _parse_response(self, data: dict[str, Any], *, model: str) -> ProviderResponse:
        content = data.get("content")
        if not isinstance(content, list):
            raise MalformedResponseError("Anthropic response missing content[]")

        text_parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(str(block.get("text", "")))

        text = "\n".join(part for part in text_parts if part).strip()
        if not text:
            raise MalformedResponseError("Anthropic response contained no text blocks")

        usage_raw = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        usage = TokenUsage(
            input_tokens=int(usage_raw.get("input_tokens", 0)),
            output_tokens=int(usage_raw.get("output_tokens", 0)),
        )
        stop_reason = data.get("stop_reason")
        return ProviderResponse(
            text=text,
            model=str(data.get("model") or model),
            usage=usage,
            stop_reason=str(stop_reason) if stop_reason is not None else None,
            raw=data,
        )
