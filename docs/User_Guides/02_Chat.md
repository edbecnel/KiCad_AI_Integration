# Chat
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › Chat


[Home](../../README.md) · [User Guides](README.md) · Chat

## Overview

**Chat** is for ad-hoc engineering questions against your KiCad project. You review a **context preview** before any data is sent to the AI provider. Multi-turn conversations are saved per project.

**Rationale:** Unlike AERF (structured stages → EKM), Chat is free-form Q&A. Use it for quick reviews, layout questions, netlist checks, and follow-up discussion.

## Who this is for

Engineers who want schematic-aware AI help without running the full eight-stage AERF pipeline.

## Before you begin

- [Getting Started](00_Getting_Started.md) complete
- **Refresh context** in the Assistant shell
- API key configured (Settings or config file)

## How to open it

- **Ctrl+1** or **Chat** tab in the Assistant shell
- CLI: `--ui-chat` or `--ui` with focus

---

## UI reference

| Control | Purpose |
|---------|---------|
| **API key** | Override config key for this session (password field) |
| **Template** | Prompt style: General review, PCB layout audit, Isolation/clearance, Netlist crosscheck, Netlist gap-fill |
| **Include schematic image** | Attach exported schematic image to the prompt (needs Poppler) |
| **Focus on KiCad selection** | Include selected PCB items when `pcbnew` is available |
| **Firmware file** / **Browse…** | Optional firmware source for cross-review prompts |
| **Schematic / PCB / BOM / ERC/DRC / Netlist** | Toggle which context layers appear in the preview |
| **Design intent (optional)** | Free-text design goals prepended to the prompt |
| **Your question** | Your message to the provider |
| **Context preview** | Read-only assembled prompt context — review before send |
| **Approve & Send** | Confirm and transmit to provider |
| **New conversation** | Clear session history for this project |
| **Conversation** | Read-only log of turns |
| Status line | Hints and send state |

---

## Step-by-step workflow

### 1. Prepare context

1. **Refresh context** in the shell header.
2. Open **Chat** (Ctrl+1).
3. Select a **Template** and context checkboxes.
4. Optionally add **Design intent** and enable **Include schematic image**.

### 2. Ask and approve

1. Type your question in **Your question**.
2. Read **Context preview**.
3. Click **Approve & Send**.
4. Confirm the transmission dialog.

**Expected result:** Response appears in **Conversation**; status shows completion or error.

### 3. Follow up

Ask another question in the same session — prior turns are included automatically.

### 4. Start fresh

Click **New conversation** to reset history (does not delete `kicad_ai/conversation.json` until next send overwrites).

---

## What gets saved

| Path | Content |
|------|---------|
| `<project>/kicad_ai/conversation.json` | Multi-turn session history |

---

## Troubleshooting

### Approve & Send disabled or no preview

Run **Refresh context** first. Check status bar for context errors.

### Focus on KiCad selection greyed out

Requires KiCad with open board (`pcbnew`). Not available in Terminal-only file-based mode.

### Empty or stale context

Save schematic/PCB in KiCad, then **Refresh context**.

---

## Limitations

- Chat output is **inference**, not curated EKM — use AERF + Notebook for persistent approved knowledge.
- Dev flag `--ask` bypasses this UI; not for end users.

---

## Related documents

- [05 — AERF](05_AERF_Staged_Analysis.md) — structured analysis
- [How AERF Works](How_AERF_Works.md)
- [10 — Security and Approval](10_Security_and_Approval.md)

## Parent

- [User Guides](README.md)