# KiCad AI Integration — Feature Overview

**What it is:** An open-source project to bring AI (Claude today, other models later) into KiCad so engineers can ask design questions against the **actual project** — schematic, parts, datasheets — instead of copying files into a generic chatbot.

**Status:** Early working prototype. Core flow is demonstrated; full Phase 1 vision is not complete.

---

## Working now

### Project understanding (schematic)
- Reads the open KiCad project schematic: components, values, footprints, references, hierarchy
- Builds structured context for AI review (not a raw file dump)

### Datasheet management
- Shared library for datasheet PDFs across projects
- Automatic resolution when PDFs exist or URLs can be fetched
- **Datasheets** panel: **Missing** and **All required** tabs; attach files, drag-and-drop, refresh, **Reset & re-resolve** per part Value, **Use AI to find datasheets** (opt-in URL suggestion + approval)
- Catalog picks up manually added PDFs in the library folder

### AI integration
- **Claude API** integration (Sonnet 4.5 supported via configuration)
- **Prompt builder** for general schematic design review (first template)
- Large schematics are summarized automatically so requests stay manageable

### User interface
- **Chat panel**: ask questions, see what will be sent, **approve before sending**, read Claude's answer and token usage
- Runs from a terminal alongside KiCad (no native KiCad menu plugin yet)
- Optional **schematic image** for visual questions (works; large designs are slow and costly — text Q&A is the reliable path today)

### Security / control
- Context **preview** before any cloud send
- **Approve & Send** gate in the chat UI (no silent upload of project data)

---

## Partially working / early

| Feature | State |
|---------|--------|
| Schematic image (multimodal) | Implemented; best for smaller scopes or lower resolution |
| Net labels from schematic | Basic label extraction |
| PCB summary | Footprint/net counts from PCB file when present |
| Netlist export | Via KiCad CLI when available |
| Developer ask shortcut | Works but bypasses approval UI — internal testing only |

---

## Not built yet (Phase 1 still open)

### Richer project context
- Full **PCB** data: tracks, vias, zones, net classes, design rules
- **BOM** extraction for AI review
- **ERC / DRC** results in context
- Full **netlist connectivity** graph for deep analysis
- User toggles for which context types to include (schematic only vs PCB vs BOM, etc.)

### More AI capabilities
- Additional **prompt templates** (layout audit, isolation/clearance, netlist cross-check)
- **Netlist gap-fill** and SUBCKT model generation from datasheets
- **AI-assisted datasheet discovery** (Claude URL suggestion when HTTPS fetch fails; opt-in via config, CLI, or Missing Datasheets panel)

### Product polish
- **Native KiCad plugin** (menu/toolbar entry, no separate terminal)
- Context preview **thumbnail** for schematic images
- **Multi-turn** conversation (history across questions)
- Token/cost display in a user-friendly way

---

## Planned later

### Phase 2 — Plugin & conversational UX
- Installable KiCad plugin
- Dockable chat window inside the editor
- Conversation history and session management
- Markdown rendering, template library
- Multiple AI provider profiles (OpenAI, local models, etc.)

### Phase 3 — Engineering assistant
- One-click audits: schematic review, PCB layout, power/signal integrity
- Component comparison and datasheet-guided analysis
- KiCad Python script and SPICE simulation assistance
- Domain workflows beyond free-form chat

---

## What you can demo today

An engineer can open a real KiCad project, launch the chat panel, ask something like *"What are the main active parts on this schematic?"* or *"Which parts are missing datasheets?"*, review what will be sent, approve it, and get a **schematic-aware** answer from Claude — without exporting or copy-pasting.

The **datasheet workflow** is also usable: identify missing PDFs, attach them, reset stale links per part Value, and refresh until resolved.

---

## Bottom line

| | |
|---|---|
| **Proven** | Schematic-aware AI Q&A with user approval; datasheet library, missing-PDF workflow, and opt-in AI datasheet discovery |
| **In progress** | Broader context (PCB, BOM, rules), more templates, production-ready UX |
| **Later** | In-editor plugin, ongoing conversations, specialized engineering audits |

This is a **foundation**, not a finished product — but the central idea (automatic context + controlled AI review inside the design flow) is working for schematic-level questions.