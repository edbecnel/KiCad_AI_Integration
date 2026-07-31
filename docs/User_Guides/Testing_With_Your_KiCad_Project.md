# Testing With Your KiCad Project

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [User Guides](README.md)

> **Status:** Maintained  
> **Applies To:** Engineers validating KiCad AI Integration against a real schematic

This guide walks through testing chat, datasheet management, AERF staged analysis, and the Engineering Notebook using **external Python scripts** — no native KiCad plugin required. KiCad does **not** need to be open; the assistant reads your saved project files from disk.

For contributor checklists and QA steps, see [E2E Full Flow](../Developer_Handbook/07_E2E_Full_Flow.md).

---

## What you need

| Requirement | Notes |
|-------------|--------|
| **KiCad 8+ project** | Saved on disk; you will pass the path to `.kicad_pro` |
| **This repository** | Clone and use `scripts/run_ai_assistant.py` |
| **Anthropic API key** | For any cloud send (chat, AERF stages). Set via env or config (below) |
| **wxPython** | Required for UI panels. On macOS Terminal: `pip install wxPython`. Inside KiCad Scripting Console, wx is bundled |
| **Python 3** | System Python with wx is fine for Terminal launch |

**Optional (improves context, not required for basic smoke):**

| Tool | Purpose |
|------|---------|
| `kicad-cli` on `PATH` | Netlist export for richer context |
| Poppler `pdftoppm` | Schematic image export (`--image`) — see [ADR-0004](../Architecture/ADRs/ADR-0004-Optional-Multimodal-Schematic-Context.md) |

---

## One-time setup

### 1. Clone the repository

```bash
git clone https://github.com/edbecnel/KiCad_AI_Integration.git
cd KiCad_AI_Integration
```

### 2. Configure API key and provider

Either set an environment variable:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or copy the example config to your home directory and edit it:

```bash
cp docs/Developer_Handbook/kicad_ai_config.example.json ~/kicad_ai_config.json
# Edit ~/kicad_ai_config.json — add your anthropic_api_key
```

Minimum config keys (see [`src/utils/config.py`](../../src/utils/config.py)):

```json
{
  "anthropic_api_key": "sk-ant-...",
  "ai_provider": "claude",
  "claude_model": "claude-3-5-sonnet-20241022",
  "artifact_library_path": "~/kicad_ai_library"
}
```

Never commit API keys. `~/kicad_ai_config.json` is gitignored.

### 3. Install wxPython (Terminal launch on macOS)

```bash
pip install wxPython
```

On Linux/Windows, use the same command if `import wx` fails when launching a UI panel.

---

## Quick smoke (no personal project)

Use the built-in test fixture to confirm context collection **without** an API call:

```bash
python scripts/run_ai_assistant.py tests/fixtures/testproj.kicad_pro
```

Expected: JSON context summary printed to the terminal, plus a line like `Summary: N symbols, … datasheets resolved`. No wx window opens.

---

## Using your own KiCad project

1. **Save** your schematic in KiCad (File → Save) so `.kicad_sch` is current on disk.
2. Note the **absolute path** to your `.kicad_pro` file, for example:
   `/Users/you/Projects/MyAmp/MyAmp.kicad_pro`
3. Run any command below with that path.

**First run side effects:**

- Creates `<project>/kicad_ai/` if missing (artifact manifest, later EKM)
- May fetch datasheet PDFs into `~/kicad_ai_library/` when URLs are present (configurable)

You do **not** need KiCad running for this workflow. Context is collected by parsing project files ([`src/context/collector.py`](../../src/context/collector.py)).

---

## Launching UI panels (Terminal — recommended)

Replace `/path/to/project.kicad_pro` with your project path.

### Chat (`--ui-chat`)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-chat
```

1. Dialog opens; API key field pre-filled from config if set.
2. Click **Refresh context** — preview shows project name, symbol count, datasheet stats.
3. Enter a question (e.g. *"What are the main active parts on this schematic?"*).
4. Review the prompt preview and estimated tokens.
5. Click **Approve & Send** — confirm in the dialog. **Cancel** must not call the API.
6. Read Claude's response and token counts.

### Datasheets (`--ui-datasheets`)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-datasheets
```

1. Open **Missing** tab — parts without resolved PDFs.
2. **Attach PDF** or use drag-and-drop for a part Value.
3. **Refresh** after changes; use **Reset & re-resolve** per Value if links are stale.

### AERF staged analysis (`--ui-aerf`)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-aerf
```

1. **Refresh context** first.
2. Circuit family defaults to `blocking_oscillator` (only full KB today). Edit the family field if you used the classifier elsewhere.
3. Set **AERF stage (0–7)**; optionally enable **Include schematic image**.
4. Click **Build preview** to see the stage prompt without sending.
5. Click **Approve & Send** — confirm transmission to the provider.
6. Repeat for stages 0–7 as needed. Completed stages accumulate for write-back.
7. When ready, click **Write to EKM…** — separate confirmation before anything is written to disk.

### Engineering Notebook (`--ui-notebook`)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-notebook
```

1. Browse collapsible EKM sections (registry-driven editors).
2. Use **Search** to find fields.
3. Edit values; click **Save** to persist.
4. **Advanced JSON** tab shows raw document (debug).

Non-modal variant (embedding path for future plugin):

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-notebook-panel
```

### Simulation / SUBCKT (`--ui-simulation`, early)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-simulation
```

Scans for missing SPICE models, can generate SUBCKT libraries and write spice fields back to the schematic. **Reload the schematic in KiCad** after file write-back.

---

## End-to-end smoke (full handover path)

This validates AERF → EKM → Notebook persistence:

1. **AERF panel** — run stages with **Approve & Send**; finish with **Write to EKM…**
   ```bash
   python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-aerf
   ```

2. **Notebook panel** — open saved sections and confirm AERF write-back content
   ```bash
   python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-notebook
   ```

3. **EKM CLI** — verify persistence on disk (use the **project directory**, not `.kicad_pro`)
   ```bash
   python scripts/ekm_tool.py show "$(dirname "/path/to/project.kicad_pro")"
   ```

   Expect JSON summary of `kicad_ai/engineering_knowledge.json`.

---

## Headless / low-cost validation (no cloud spend)

These commands build prompts and inspect EKM **without** calling Anthropic (unless you add `--approve-send`).

### Context only

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro"
```

### AERF stage-0 plan (dry run)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --aerf-plan
```

Optional family override:

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" \
  --aerf-plan --aerf-family blocking_oscillator
```

### Single AERF stage prompt (no send)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --aerf-stage 0
```

Add `--approve-send` only when you intend to call the provider.

### Full pipeline dry run (stages 0–7, no cloud)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --aerf-pipeline
```

### EKM write-back plan (preview only)

After saving stage JSON envelopes to a file (e.g. from a prior run):

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" \
  --aerf-writeback-plan --aerf-stages-json /path/to/stages.json
```

Add `--approve-ekm-writeback` to persist to `engineering_knowledge.json`.

### EKM CLI

Pass the **project directory** (folder containing `.kicad_pro`) or the path to `engineering_knowledge.json`:

```bash
python scripts/ekm_tool.py init "/path/to/project_directory"
python scripts/ekm_tool.py validate "/path/to/project_directory"
python scripts/ekm_tool.py show "/path/to/project_directory"
```

Example with a `.kicad_pro` path:

```bash
PROJECT="/path/to/MyAmp.kicad_pro"
python scripts/ekm_tool.py show "$(dirname "$PROJECT")"
```

### Dev-only bypass (not for production testing)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" \
  --ask "Summarize active parts"
```

`--ask` **skips** the Approve & Send UI. Use only for local development.

---

## Security and approval gates

Two independent gates protect your data:

| Gate | What it controls | UI / CLI |
|------|------------------|----------|
| **Cloud send** | Transmission to Anthropic | **Approve & Send** in chat/AERF; CLI `--approve-send` |
| **EKM write-back** | Writes to `<project>/kicad_ai/engineering_knowledge.json` | **Write to EKM…** in AERF UI; CLI `--approve-ekm-writeback` |

Project files are read from disk for context collection; nothing is sent to the cloud until you explicitly approve.

---

## Alternative launch: KiCad Scripting Console

If you prefer running inside KiCad:

1. Open **KiCad PCB Editor** (`pcbnew`) with your project.
2. **Tools → Scripting Console**
3. Run:

```python
exec(open("/absolute/path/to/KiCad_AI_Integration/scripts/run_ai_assistant.py").read())
main_ui_chat("/absolute/path/to/project.kicad_pro")
```

Other panels: `main_ui_aerf(...)`, `main_ui_notebook(...)`, `main_ui_datasheets(...)`, etc. (defined in the same script).

**Note:** On macOS, Scripting Console paste/focus can be unreliable — **Terminal launch is recommended** for UI testing.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `wxPython is required` | wx not installed for your Terminal Python | `pip install wxPython`, or run from KiCad Scripting Console |
| `No project path` | Missing `.kicad_pro` argument | Pass full path to `.kicad_pro` |
| `Provider error` / auth failure | Missing or invalid API key | Set `ANTHROPIC_API_KEY` or `anthropic_api_key` in `~/kicad_ai_config.json` |
| 0 symbols in summary | Schematic not saved or wrong path | Save in KiCad; verify `.kicad_sch` exists beside `.kicad_pro` |
| Schematic edits not visible | Stale files on disk | Save schematic; re-run **Refresh context** |
| Simulation write-back not in editor | File changed on disk | Reload schematic in KiCad |
| AERF KB content mismatch | Wrong circuit family | Use `blocking_oscillator` or `--aerf-family blocking_oscillator` |
| Image export fails | Poppler missing | `brew install poppler` (macOS) or skip `--image` |
| Netlist missing in context | `kicad-cli` not on PATH | Install KiCad CLI tools or set `kicad_cli` in config |

---

## Related documents

- [Feature Overview](Feature_Overview.md) — what works today
- [First-Time Setup](../Developer_Handbook/00_First_Time_Setup.md) — contributor environment
- [E2E Chat UI](../Developer_Handbook/06_E2E_Chat_UI.md) — chat-specific checklist
- [E2E Full Flow](../Developer_Handbook/07_E2E_Full_Flow.md) — contributor QA checklists
- [Glossary](../Reference/Glossary.md) — AERP, EKM, AERF, EIE acronyms

## Parent

- [User Guides](README.md)
