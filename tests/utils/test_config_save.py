"""Tests for settings persistence."""

from __future__ import annotations

from utils.config import AppConfig, save_config, load_config


def test_save_and_load_config_round_trip(tmp_path, monkeypatch) -> None:
    path = tmp_path / "kicad_ai_config.json"
    monkeypatch.setattr("utils.config.default_config_path", lambda: path)

    cfg = AppConfig(ai_provider="ollama", ollama_model="mistral")
    save_config(cfg, path)
    loaded = load_config(path)
    assert loaded.ai_provider == "ollama"
    assert loaded.ollama_model == "mistral"
