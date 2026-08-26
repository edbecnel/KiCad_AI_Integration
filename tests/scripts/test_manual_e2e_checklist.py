"""Tests for manual E2E checklist helper."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manual_e2e_checklist import collect_config_checks, collect_shell_env_checks


def test_collect_shell_env_checks_reports_path_lookups(monkeypatch) -> None:
    monkeypatch.delenv("FREEROUTING_JAR", raising=False)
    monkeypatch.delenv("FREEROUTING_CLI", raising=False)
    monkeypatch.setattr(
        "scripts.manual_e2e_checklist.shutil.which",
        lambda name: "/opt/homebrew/bin/ngspice" if name == "ngspice" else None,
    )

    checks = collect_shell_env_checks()

    assert checks["FREEROUTING_JAR"] is None
    assert checks["ngspice (PATH)"] == "/opt/homebrew/bin/ngspice"


def test_collect_config_checks_reads_config_file(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "kicad_ai_config.json"
    config_path.write_text(
        json.dumps(
            {
                "routing_enabled": True,
                "freerouting_cli": "/Applications/freerouting.app/Contents/MacOS/freerouting",
                "kicad_cli": "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
                "anthropic_api_key": "sk-ant-test",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KICAD_AI_CONFIG", str(config_path))
    monkeypatch.delenv("FREEROUTING_JAR", raising=False)
    monkeypatch.delenv("FREEROUTING_CLI", raising=False)
    resolved_cli = Path("/Applications/freerouting.app/Contents/MacOS/freerouting")

    def _fake_resolve(**kwargs):
        class R:
            installed = True
            jar_path = None
            cli_path = resolved_cli

        return R()

    monkeypatch.setattr("utils.freerouting_cli.try_resolve_freerouting", _fake_resolve)

    checks = collect_config_checks()

    assert str(config_path) in checks["config_file"]
    assert checks["routing_enabled"] == "true"
    assert "freerouting.app" in checks["freerouting_cli (config)"]
    assert checks["anthropic_api_key (config)"] == "(set)"
    assert "KiCad.app" in checks["kicad-cli (effective)"]
