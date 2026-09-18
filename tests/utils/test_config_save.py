"""Tests for settings persistence."""

from __future__ import annotations

from utils.config import AppConfig, resolve_claude_model, save_config, load_config


def test_resolve_claude_model_maps_retired_sonnet_35() -> None:
    assert resolve_claude_model("claude-3-5-sonnet-20241022") == "claude-sonnet-4-6"
    assert resolve_claude_model("claude-sonnet-4-6") == "claude-sonnet-4-6"


def test_from_dict_maps_deprecated_claude_model() -> None:
    cfg = AppConfig.from_dict({"claude_model": "claude-3-5-sonnet-20241022"})
    assert cfg.claude_model == "claude-sonnet-4-6"


def test_save_and_load_config_round_trip(tmp_path, monkeypatch) -> None:
    path = tmp_path / "kicad_ai_config.json"
    monkeypatch.setattr("utils.config.default_config_path", lambda: path)

    cfg = AppConfig(ai_provider="ollama", ollama_model="mistral")
    save_config(cfg, path)
    loaded = load_config(path)
    assert loaded.ai_provider == "ollama"
    assert loaded.ollama_model == "mistral"
