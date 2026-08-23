# Configuration Reference
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › Configuration Reference


[Home](../../README.md) · [User Guides](README.md) · Configuration Reference

## Overview

Runtime settings load from **`~/kicad_ai_config.json`** (override with `KICAD_AI_CONFIG` env var). The Assistant **Settings…** dialog edits a subset; other keys require editing the JSON file directly.

## Config file location

```text
~/kicad_ai_config.json
```

Example template: [docs/Developer_Handbook/kicad_ai_config.example.json](../Developer_Handbook/kicad_ai_config.example.json)

---

## Settings dialog (UI)

| Field | Config key | Purpose |
|-------|------------|---------|
| Provider | `ai_provider` | `claude` or `ollama` |
| Anthropic API key | `anthropic_api_key` | Claude API key |
| Claude model | `claude_model` | Model id (e.g. `claude-3-5-sonnet-20241022`) |
| Ollama base URL | `ollama_base_url` | Default `http://localhost:11434` |
| Ollama model | `ollama_model` | Local model name |

---

## Full key reference

| Key | Default | Purpose | UI |
|-----|---------|---------|-----|
| `artifact_library_path` | `~/kicad_ai_library` | Shared datasheet PDF library | Config file |
| `datasheet_search_paths` | `[]` | Extra PDF search directories | Config file |
| `schematic_image_dpi` | `600` | Schematic export resolution | Config file |
| `datasheet_url_fetch` | `if_missing` | `if_missing` / `always` / `never` | Config file |
| `url_fetch_timeout_sec` | `10` | HTTPS connect timeout | Config file |
| `url_fetch_read_timeout_sec` | `60` | HTTPS read timeout | Config file |
| `url_fetch_warmup` | `true` | Warmup fetch behavior | Config file |
| `kicad_cli` | `null` | Path to `kicad-cli` binary | Config file |
| `anthropic_api_key` | env / null | Claude API key | Settings + config |
| `ai_provider` | `claude` | `claude` or `ollama` | Settings + config |
| `claude_model` | `claude-3-5-sonnet-20241022` | Claude model | Settings + config |
| `ollama_base_url` | `http://localhost:11434` | Ollama server | Settings + config |
| `ollama_model` | `llama3.2` | Ollama model | Settings + config |
| `provider_timeout_sec` | `120` | Provider connect timeout | Config file |
| `provider_read_timeout_sec` | `600` | Provider read timeout | Config file |
| `provider_max_tokens` | `4096` | Max response tokens | Config file |
| `datasheet_ai_discovery` | `false` | Enable AI URL discovery | Config file + Datasheets checkbox |
| `datasheet_ai_discovery_auto_fetch` | `false` | Auto-download after AI URL | Config file |
| `datasheet_ai_discovery_max_urls` | `3` | Max URLs per AI discovery | Config file |
| `datasheet_reset_quarantine_local_pdf` | `true` | Quarantine on reset | Config file |
| `datasheet_write_symbol_url` | `false` | Write URL to symbol field | Config file + Datasheets checkbox |
| `spice_write_symbol_fields` | `true` | Write Sim.* on simulation apply | Config file |
| `learning_auto_promote` | `true` | Promote EKM to family library after write-back | Config file |
| `learning_min_confidence` | `high` | Promotion confidence threshold | Config file |
| `learning_library_subdir` | `circuit_families` | Library subfolder name | Config file |
| `freerouting_jar` | `null` | Path to Freerouting JAR | Config file |
| `freerouting_cli` | `null` | Path to Freerouting CLI | Config file |
| `routing_enabled` | `false` | Enable Routing tab autoroute | Config file |
| `routing_timeout_sec` | `600` | Autoroute timeout | Config file |

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Fallback API key if not in config file |
| `KICAD_AI_CONFIG` | Alternate config file path |

---

## Shell preferences (separate file)

`~/kicad_ai_shell_prefs.json` — last active tab per project (managed automatically).

---

## Related documents

- [00 — Getting Started](00_Getting_Started.md)
- [08 — PCB Routing](08_PCB_Routing.md)
- [03 — Datasheets](03_Datasheets.md)

## Parent

- [User Guides](README.md)