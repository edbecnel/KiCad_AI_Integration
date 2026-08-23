# Testing With Your KiCad Project
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › Testing With Your KiCad Project


[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [User Guides](README.md)

> **Status:** Maintained
> **Owner:** Project maintainers
> **Applies To:** Engineers validating KiCad AI Integration against a real schematic
> **Last Reviewed:** 2026-08-07
> **Review Frequency:** Quarterly

This guide is a **validation checklist** for contributors and power users. For install and everyday usage, start at [Getting Started](00_Getting_Started.md) and the [User Guides hub](README.md).

You can validate using the **KiCad ActionPlugin** (recommended) or **Terminal** `scripts/run_ai_assistant.py`. Both use the same seven-tab Assistant shell. Context is read from **saved project files on disk** — save in KiCad before **Refresh context**.

For contributor E2E steps, see [E2E Full Flow](../Developer_Handbook/07_E2E_Full_Flow.md). For how staged AERF analysis works, see [How AERF Works](How_AERF_Works.md).

---

## Authority boundaries (facts vs inference)

| Store | Role in analysis |
|-------|------------------|
| KiCad files / `ProjectContext` | Extracted facts (symbols, nets, netlist summary) |
| Circuit Family KB | Reference knowledge for the matched family |
| EKM | Author-approved project knowledge and design intent |
| AERF stage JSON | Per-run reasoning (transient until EKM write-back) |
| LLM (Chat or AERF) | Engineering inference — classify statements; flag unknowns |

**Chat** (`--ui-chat`) uses the `general_review` template (ad-hoc Q&A). **AERF** (`--ui-aerf`) runs eight staged LLM calls with structured JSON output.

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
| `kicad-cli` | Set `kicad_cli` in `~/kicad_ai_config.json` (see [example](../Developer_Handbook/kicad_ai_config.example.json)) or on `PATH` — netlist export |
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

## Launch the assistant (recommended — no path on command line)

After setup, open the **launcher** — pick your project, refresh context in the UI, then open Chat, Simulation, AERF, etc.:

```bash
python scripts/run_ai_assistant.py --ui
```

Optional: pre-fill a project path:

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui
```

In the unified Assistant shell:

1. Click **Browse…** to select a `.kicad_pro` file (or pass the path on the command line).
2. Click **Refresh context** — the summary shows symbols, datasheets, **SPICE netlist status**, PCB counts, and simulation gaps.
3. Use the **Chat**, **Datasheets**, **Simulation**, **AERF**, **Notebook**, **Audits**, or **Routing** tabs (or `Ctrl+1` … `Ctrl+7`).

You do **not** need shell commands to verify netlist export — look for a line like `SPICE netlist: 22 lines (partial — …)` in the context summary.

### KiCad plugin entry (recommended in-editor)

Install the ActionPlugin per [Development Environment](../Developer_Handbook/01_Development_Environment.md#kicad-actionplugin-phase-2), then in **KiCad PCB Editor** use **Tools → External Plugins → KiCad AI Assistant**. The unified shell opens as a non-modal window parented to the editor (same tabs as `--ui`).

### Known UX limitation

True wxAUI docking inside the PCB editor is deferred. The plugin uses a separate non-modal Assistant frame. On **macOS full screen**, exit full screen (**Control+Command+F**) or use Terminal `--ui` if the window does not appear.

**`--ui` and the ActionPlugin** open the unified Assistant shell with all tabs embedded. Use the **Datasheets** tab (not Chat) for PDF attach and AI discovery. Chat supports **multi-turn** follow-up questions; history is saved to `kicad_ai/conversation.json` per project (**New conversation** resets it).

---

## Quick smoke (no personal project, no UI)

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

## Launching individual panels (optional)

If you already know your project path, you can open a panel directly. The **launcher** (`--ui`) is still the recommended entry point.

Replace `/path/to/project.kicad_pro` with your project path.

### Chat (`--ui-chat`)

```bash
python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui-chat
```

1. Dialog opens; API key field pre-filled from config if set.
2. Click **Refresh context** — preview shows project name, symbol count, datasheet stats, **SPICE netlist status**, and PCB summary.
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

1. Open **KiCad PCB Editor** (`pcbnew`) with your project and **save** the board.
2. **Tools → Scripting Console**
3. Run:

```python
import sys; sys.path.insert(0, "/absolute/path/to/KiCad_AI_Integration/src"); from ui.launcher import show_assistant_shell; show_assistant_shell()
```

With a saved board open, the Assistant **auto-selects** the project (no Browse step). Or load the CLI script and call a panel directly:

```python
exec(open("/absolute/path/to/KiCad_AI_Integration/scripts/run_ai_assistant.py").read())
main_ui_launcher()  # or main_ui_chat(), main_ui_aerf(), etc.
```

**Note:** On macOS, Scripting Console paste/focus can be unreliable — **Terminal launch is recommended** for UI testing.

**macOS full screen:** If the PCB editor is full screen, the Assistant cannot open as a separate window on top of it (same limitation as KiPython). Exit full screen (**Control+Command+F**) and launch again, or use Terminal:

```bash
PYTHONPATH=src python scripts/run_ai_assistant.py "/path/to/project.kicad_pro" --ui
```

A dockable in-editor panel is planned (Phase 2 plugin).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Assistant does nothing / no window (Scripting Console, macOS) | PCB editor is **full screen** — macOS blocks overlay windows | Exit full screen (**Control+Command+F**), or launch from Terminal with `--ui` |
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

## E2E sign-off checklist (automated + manual)

Automated coverage (run `PYTHONPATH=src pytest`):

- AERF stage prompts include methodology and output schema sections
- Stage output JSON validation (`tests/reasoning/test_stage_schemas.py`)
- AERF pipeline mock provider (`tests/inference/test_aerf_pipeline.py`)
- Bedini local project when present (`tests/integration/test_bedini_aerf_exit.py`)
- Live Bedini stage fixtures (`tests/integration/test_bedini_aerf_live.py`, no API)
- PCB extraction fixture (`tests/context/test_pcb_extract.py`)

Manual sign-off (your schematic):

Use the [AERF Validation Rubric](AERF_Validation_Rubric.md) when reviewing live stage JSON.

1. `--ui` → Assistant shell → Refresh context
2. `--ui-aerf` → stages 0–7 with Approve & Send → Write to EKM
3. `--ui-notebook` → verify EKM sections
4. Optional Chat smoke test (ad-hoc Q&A, not AERF)
5. **Audits tab** (Ctrl+6): run schematic or PCB layout review; confirm `kicad_ai/reviews/*.json` saved
6. **Live context** (KiCad plugin only): open PCB, enable **Focus on KiCad selection** in Chat; run **Explain DRC** if `kicad-cli` is on PATH
7. **Routing tab** (Ctrl+7): configure Freerouting + `routing_enabled`; run autoroute, review DRC, Accept/Reject candidate

### Routing prerequisites (Freerouting KiCad plugin NOT required)

KAI uses headless Freerouting plus pcbnew DSN/SES — not the interactive Content Manager plugin.

| Prerequisite | Required for E2E? | Notes |
|---|---|---|
| Freerouting KiCad plugin | **No** | Out of scope; use standalone JAR/CLI |
| KiCad AI Integration (pcbnew) | **Yes** | DSN export / SES import |
| Standalone Freerouting (JAR or CLI) | **Yes** | `freerouting_jar` / `freerouting_cli` in config or env |
| `routing_enabled: true` | **Yes** | Opt-in; defaults to `false` |
| Open `.kicad_pcb` in PCB Editor | **Yes** | Board must be loaded in pcbnew |
| `kicad-cli pcb drc` | Recommended | Post-route validation via shared `run_live_drc()` |

CLI: `--ui-routing` opens the Assistant shell on the Routing tab.

Optional E2E: `FREEROUTING_JAR=/path/to/freerouting.jar pytest -m kicad tests/integration/test_routing_e2e.py`

### Live KiCad features (plugin or Scripting Console)

These require KiCad with `pcbnew` in-process. CI uses mocked `pcbnew` stubs.

| Feature | Where | Requirement |
|---------|-------|-------------|
| Editor / board paths | Auto on Refresh context | Open `.kicad_pcb` in PCB Editor |
| Live board settings | `live_context` in prompts | Open board in pcbnew |
| Live DRC | ERC/DRC summary + Explain DRC audit | `kicad_cli` in config; `.kicad_pcb` on disk |
| Selection focus | Chat checkbox | Select footprints/nets in PCB Editor |
| Firmware cross-review | Chat firmware browse | Any text file (e.g. `main.py`) |

CLI shortcuts: `--audit-schematic` or `--audit-pcb` opens the Assistant shell on the Audits tab; `--ui-routing` opens the Routing tab.

---

## Related documents

- [Feature Overview](Feature_Overview.md) — what works today
- [How AERF Works](How_AERF_Works.md) — staged analysis vs Chat and copy-paste workflows
- [ADP-011: Assistant Shell UI](../Architecture/ADP-011-Assistant-Shell-UI.md) — unified tabbed shell (`--ui`)
- [First-Time Setup](../Developer_Handbook/00_First_Time_Setup.md) — contributor environment
- [E2E Chat UI](../Developer_Handbook/06_E2E_Chat_UI.md) — chat-specific checklist
- [E2E Full Flow](../Developer_Handbook/07_E2E_Full_Flow.md) — contributor QA checklists
- [Glossary](../Reference/Glossary.md) — AERP, EKM, AERF, EIE acronyms

## Parent

- [User Guides](README.md)