# E2E Validation — Full Flow (Chat, Datasheets, AERF, Notebook)

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md) · [Developer Handbook](README.md)

> **Status:** Maintained  
> **Owner:** Project maintainers  
> **Applies To:** Manual validation and QA of Phase 1 host features

End-user walkthrough: [Testing With Your KiCad Project](../User_Guides/Testing_With_Your_KiCad_Project.md).

> **Future UI:** A unified tabbed Assistant shell will replace the launcher + separate modal panels. Until then, validate each feature via its `--ui-*` flag or launcher button. See [ADP-011](../Architecture/ADP-011-Assistant-Shell-UI.md).

## Prerequisites

- Repository cloned; `~/kicad_ai_config.json` or `ANTHROPIC_API_KEY` set (see [kicad_ai_config.example.json](kicad_ai_config.example.json))
- wxPython: `pip install wxPython` for Terminal UI on macOS
- Test project: `tests/fixtures/testproj.kicad_pro` (no API) or a real `.kicad_pro`
- KiCad **not** required to be open — context is file-based ([`src/context/collector.py`](../../src/context/collector.py))

## Terminal launch pattern

```bash
REPO=/path/to/KiCad_AI_Integration
PROJECT=/path/to/project.kicad_pro

python "$REPO/scripts/run_ai_assistant.py" "$PROJECT" --ui-chat
```

---

## 1. Context collection (no UI, no API)

```bash
python scripts/run_ai_assistant.py tests/fixtures/testproj.kicad_pro
```

- [ ] JSON context prints without error
- [ ] Summary line reports symbol count
- [ ] No cloud request made

---

## 2. Chat UI (`--ui-chat`)

See also [06_E2E_Chat_UI.md](06_E2E_Chat_UI.md).

```bash
python scripts/run_ai_assistant.py "$PROJECT" --ui-chat
```

- [ ] Dialog opens; API key pre-filled from config (masked)
- [ ] **Refresh context** populates preview
- [ ] Optional **Include schematic image** updates byte-size when export succeeds
- [ ] Prompt preview and token estimate update when question changes
- [ ] **Approve & Send** → **Cancel** does not call Anthropic
- [ ] **Approve & Send** → **Yes** returns response with token counts
- [ ] **Close** exits cleanly

---

## 3. Datasheets UI (`--ui-datasheets`)

```bash
python scripts/run_ai_assistant.py "$PROJECT" --ui-datasheets
```

- [ ] **Missing** tab lists unresolved required datasheets
- [ ] **All required** tab shows full set
- [ ] **Attach PDF** imports into shared library
- [ ] **Refresh** updates resolution status
- [ ] **Reset & re-resolve** clears stale cache for one Value

CLI reset (optional):

```bash
python scripts/run_ai_assistant.py "$PROJECT" --reset-datasheet "PART_VALUE"
```

---

## 4. AERF staged analysis

### 4a. Dry run (no cloud)

```bash
python scripts/run_ai_assistant.py "$PROJECT" --aerf-plan
python scripts/run_ai_assistant.py "$PROJECT" --aerf-stage 0
python scripts/run_ai_assistant.py "$PROJECT" --aerf-pipeline
```

- [ ] Stage-0 plan prints family id, token estimate, prompt excerpt
- [ ] `--aerf-stage N` without `--approve-send` builds prompt only
- [ ] `--aerf-pipeline` without `--approve-send` reports dry-run

### 4b. UI (`--ui-aerf`)

```bash
python scripts/run_ai_assistant.py "$PROJECT" --ui-aerf
```

- [ ] **Refresh context** succeeds
- [ ] **Build preview** shows stage prompt without send
- [ ] **Approve & Send** on stage N → confirmation → provider response
- [ ] Completed stage count increments; stage spinner can advance
- [ ] **Write to EKM…** disabled until at least one stage completes
- [ ] **Write to EKM…** shows field preview; **No** cancels disk write
- [ ] **Write to EKM…** → **Yes** writes `kicad_ai/engineering_knowledge.json`

### 4c. CLI pipeline with approval (optional, uses API credits)

```bash
python scripts/run_ai_assistant.py "$PROJECT" \
  --aerf-pipeline --approve-send --aerf-family blocking_oscillator
```

- [ ] Pipeline completes or reports `failed_at_stage`
- [ ] `--aerf-writeback-plan` previews EKM diff from completed stages
- [ ] `--approve-ekm-writeback` persists when combined with pipeline

---

## 5. Engineering Notebook

### Modal (`--ui-notebook`)

```bash
python scripts/run_ai_assistant.py "$PROJECT" --ui-notebook
```

- [ ] Sections render (collapsible)
- [ ] **Search** filters fields
- [ ] Edit + **Save** persists changes
- [ ] **Advanced JSON** tab shows document
- [ ] **Reload** picks up external EKM changes

### Non-modal (`--ui-notebook-panel`)

```bash
python scripts/run_ai_assistant.py "$PROJECT" --ui-notebook-panel
```

- [ ] Frame stays open alongside terminal
- [ ] Same save/reload behavior as modal

---

## 6. EKM CLI

```bash
PROJECT_DIR="$(dirname "$PROJECT")"
python scripts/ekm_tool.py init "$PROJECT_DIR"
python scripts/ekm_tool.py validate "$PROJECT_DIR"
python scripts/ekm_tool.py show "$PROJECT_DIR"
```

- [ ] `init` creates `kicad_ai/engineering_knowledge.json` if missing
- [ ] `validate` exits 0 on schema-compliant document
- [ ] `show` prints JSON summary after AERF write-back

> `ekm_tool` expects a project **directory** or EKM JSON file — not a `.kicad_pro` path directly.

---

## 7. Simulation panel (early, optional)

```bash
python scripts/run_ai_assistant.py "$PROJECT" --ui-simulation
```

- [ ] Gap scan lists parts missing SPICE models
- [ ] SUBCKT generation path reachable (may require API key)
- [ ] After schematic write-back, reload schematic in KiCad editor

---

## 8. Full handover smoke (AERF → EKM → Notebook)

1. `--ui-aerf` → stages with **Approve & Send** → **Write to EKM…**
2. `--ui-notebook` → verify written sections
3. `python scripts/ekm_tool.py show "$(dirname "$PROJECT")"`

- [ ] EKM file exists and validates
- [ ] Notebook displays AERF-authored fields

---

## Automated tests (no KiCad, no wx)

```bash
pytest tests/ekm/ tests/inference/ -q
```

Broader platform tests:

```bash
pytest tests/prompts/ tests/context/ tests/reasoning/ -q
```

Bedini AERF exit (local `Bedini_SSG_Radiant_Oscillator.kicad_pro` when present):

```bash
pytest tests/integration/test_bedini_aerf_exit.py -q
```

See [05_Testing.md](05_Testing.md) for philosophy and coverage expectations.

---

## Security checklist

- [ ] No API transmission before **Approve & Send** (`--ui-chat`, `--ui-aerf`)
- [ ] No EKM disk write before **Write to EKM…** or `--approve-ekm-writeback`
- [ ] `--ask` documented as dev-only bypass
- [ ] Context preview visible before cloud send in UI panels

---

## Parent

- [Developer Handbook](README.md)

## Related Documents

- [Testing With Your KiCad Project](../User_Guides/Testing_With_Your_KiCad_Project.md)
- [ADP-011: Assistant Shell UI](../Architecture/ADP-011-Assistant-Shell-UI.md) — Assistant shell scaffold (`--ui`)
- [E2E Chat UI](06_E2E_Chat_UI.md)
- [Testing](05_Testing.md)
- [Feature Overview](../User_Guides/Feature_Overview.md)
