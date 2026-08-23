# Getting Started
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › Getting Started


[Home](../../README.md) · [User Guides](README.md) · Getting Started

## Overview

Install the KiCad AI Assistant, configure your API key, and run your first **Refresh context** against a saved KiCad project. This guide is written for **KiCad ActionPlugin** users first; a Terminal launch path is included as an alternative.

## Who this is for

Engineers using KiCad 8+ who want schematic-aware AI chat, datasheet management, staged analysis (AERF), and related tools without copying files into a generic chatbot.

## Before you begin

| Requirement | Notes |
|-------------|--------|
| **KiCad 8+** | With a saved `.kicad_pro` project |
| **This repository** | Clone or install the plugin (see below) |
| **Anthropic API key** | For cloud AI features (Chat, AERF, Audits, AI datasheet discovery). Optional if using Ollama locally |
| **wxPython** | Bundled with KiCad; for Terminal-only use: `pip install wxPython` |
| **markdown** | For formatted in-app Help viewer: `pip install markdown` (optional fallback renders plain structure) |

**Optional (improves context):**

| Tool | Purpose |
|------|---------|
| `kicad-cli` | Netlist export, DRC — set in config or on `PATH` |
| Poppler `pdftoppm` | Schematic image export for multimodal prompts |
| Freerouting JAR/CLI | PCB autorouting ([08 — PCB Routing](08_PCB_Routing.md)) |
| ngspice | KiCad Simulator after SUBCKT setup |

---

## Instructions

### 1. Install the ActionPlugin

1. Clone the repository:

   ```bash
   git clone https://github.com/edbecnel/KiCad_AI_Integration.git
   cd KiCad_AI_Integration
   ```

2. Find your KiCad plugins folder. In **PCB Editor → Tools → Scripting Console**:

   ```python
   import pcbnew
   print(pcbnew.PLUGIN_DIRECTORIES_SEARCH)
   ```

3. Symlink the plugin package (adjust paths for your OS):

   ```bash
   ln -s /path/to/KiCad_AI_Integration/src/plugin/kicad_ai_assistant \
     ~/Documents/KiCad/9.0/scripting/plugins/kicad_ai_assistant
   ```

   Or copy the `kicad_ai_assistant` folder into that directory.

4. Set `KICAD_AI_SRC` to the repository `src` folder if your install method requires it (see [Developer Handbook — Development Environment](../Developer_Handbook/01_Development_Environment.md)).

5. Restart KiCad PCB Editor.

**Expected result:** **Tools → External Plugins → KiCad AI Assistant** appears in the menu.

### 2. Configure your API key

**Option A — Settings dialog (recommended after first launch):**

1. Open the Assistant → **Settings…**
2. Enter **Anthropic API key** and **Claude model**
3. Click **Save** (writes `~/kicad_ai_config.json`)

**Option B — Config file:**

```bash
cp docs/Developer_Handbook/kicad_ai_config.example.json ~/kicad_ai_config.json
# Edit anthropic_api_key and other keys
```

**Option C — Environment variable:**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

For Ollama (local, no cloud send), set `"ai_provider": "ollama"` in the config file. See [09 — Configuration Reference](09_Configuration_Reference.md).

### 3. Open the Assistant from KiCad

1. Open your project in **PCB Editor** and **save** the board (`.kicad_pcb`).
2. **Tools → External Plugins → KiCad AI Assistant**.
3. Confirm the **Project** path points to your `.kicad_pro` file (auto-filled when a saved board is open).
4. Click **Refresh context**.

**Expected result:** The summary panel shows symbol count, datasheet status, netlist lines, and estimated context tokens. Status bar: `Context ready — YourProject.kicad_pro`.

Click **Help** in the header (or **?** on a tab) to open the in-app User Guide.

### 4. Try Chat

1. Press **Ctrl+1** or select the **Chat** tab.
2. Enter a question in **Your question**.
3. Review **Context preview**.
4. Click **Approve & Send** and confirm.

See [02 — Chat](02_Chat.md) for templates, multi-turn history, and context toggles.

### 5. Alternative: Terminal launch

When KiCad full-screen blocks auxiliary windows (common on macOS), use Terminal:

```bash
pip install wxPython   # if not already installed
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui
```

Deep-link to a tab:

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-datasheets
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-aerf
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-routing
```

---

## What gets created on disk

Per project, under `<project>/kicad_ai/`:

| File / folder | Created by |
|---------------|------------|
| `engineering_knowledge.json` | AERF **Write to EKM…** / Notebook **Save** |
| `conversation.json` | Chat multi-turn sessions |
| `reviews/` | Audits and post-route AI review |
| Routing checkpoints | Routing tab accept/reject workflow |

Shared datasheet PDF library (default): `~/kicad_ai_library/`

---

## Troubleshooting

### Plugin does not appear in menu

- Verify symlink path matches `PLUGIN_DIRECTORIES_SEARCH`
- Restart KiCad after install
- Check Scripting Console for import errors

### Assistant window hidden on macOS full screen

Exit KiCad full screen (**Control+Command+F**) or launch from Terminal with `--ui`.

### 0 symbols in summary

Save the schematic in KiCad; verify `.kicad_sch` exists beside `.kicad_pro`; click **Refresh context** again.

### `ImportError` on plugin load

KiCad embeds Python 3.9. Ensure you are on a current plugin build (see [11 — Troubleshooting](11_Troubleshooting.md)).

---

## Limitations

- Context is read from **saved files on disk**, not live unsaved editor state — save before **Refresh context**.
- True dockable panel inside the PCB canvas is not yet available; the Assistant opens as a separate non-modal window.
- Some settings (routing, datasheet policies) are config-file only — not in the Settings dialog.

---

## Related documents

- [01 — Assistant Shell](01_Assistant_Shell.md)
- [09 — Configuration Reference](09_Configuration_Reference.md)
- [10 — Security and Approval](10_Security_and_Approval.md)
- [Feature Overview](Feature_Overview.md)

## Parent

- [User Guides](README.md)