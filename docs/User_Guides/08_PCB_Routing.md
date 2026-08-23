# PCB Routing
[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [User Guides](README.md) › PCB Routing


[Home](../../README.md) · [User Guides](README.md) · PCB Routing

## Overview

The **Routing** tab runs **Freerouting** autoroute with **checkpoint accept/reject** — routed results are not applied to your board until you explicitly **Accept candidate**. Optional **Post-route AI review** produces structured findings like the Audits tab.

**Rationale:** Autorouting can overwrite manual work. The checkpoint workflow keeps your authoritative `.kicad_pcb` safe until you approve the candidate.

## Who this is for

PCB designers using Freerouting with KiCad who want policy-aware routing and optional AI post-review.

## Before you begin

| Requirement | Notes |
|-------------|--------|
| **Saved `.kicad_pcb`** | Beside `.kicad_pro` |
| **`routing_enabled: true`** | In `~/kicad_ai_config.json` (not in Settings dialog) |
| **Freerouting** | `freerouting_jar` or `freerouting_cli` in config |
| **`pcbnew`** | For DSN/SES exchange when running from KiCad |
| **Refresh context** | Loads routing policy and engine status |

See [09 — Configuration Reference](09_Configuration_Reference.md).

## How to open it

- **Ctrl+7** or **Routing** tab
- CLI: `--ui-routing`

---

## UI reference

| Control | Purpose |
|---------|---------|
| **Engine** line | Freerouting install status and version |
| **Routing policy / exclusions** | Read-only policy text (nets/classes to exclude) |
| **Run autoroute** | Start Freerouting after approval dialog |
| **Accept candidate** | Promote checkpoint route to authoritative PCB |
| **Reject candidate** | Discard checkpoint without changing board |
| **Post-route AI review** | AI review of routed board (needs API key) |
| **Output** panel | Quality report, logs, metrics (read-only) |
| Status line | Phase hints and errors |

Accept/Reject/Post-route review enable only when a candidate exists.

---

## Step-by-step workflow

### 1. Prepare

1. Set `routing_enabled: true` and Freerouting paths in config.
2. Save PCB in KiCad.
3. **Refresh context** → open **Routing** (Ctrl+7).
4. Confirm **Engine: freerouting (installed)**.

### 2. Autoroute

1. Review **Routing policy / exclusions**.
2. Click **Run autoroute** → approve.
3. Wait for completion — **Output** shows quality report.

### 3. Accept or reject

- **Accept candidate** → replaces working `.kicad_pcb` with routed result (confirm).
- **Reject candidate** → discards checkpoint; board unchanged.

### 4. Optional AI review

After a successful route, **Post-route AI review** → approve → findings in **Output** and `kicad_ai/reviews/`.

See [Workflow: PCB Review and Route](Workflows/PCB_Layout_Review_and_Route.md).

---

## What gets saved

| Path | Content |
|------|---------|
| Routing checkpoint files | Under project `kicad_ai/` (checkpoint workflow) |
| `<project>/kicad_ai/reviews/` | Post-route AI review JSON |
| `.kicad_pcb` | Updated only on **Accept candidate** |

---

## Troubleshooting

### Run autoroute disabled

Engine not installed, `routing_enabled` false, or missing `.kicad_pcb` — check **Engine** line and config.

### Freerouting not found

Set `freerouting_jar` to full path of Freerouting JAR in `~/kicad_ai_config.json`.

### DSN/SES errors

Run from KiCad with board open (`pcbnew` available) or check Freerouting CLI logs in **Output**.

---

## Limitations

- Routing settings are not in the Settings dialog — edit config file.
- KiCad's built-in Freerouting **plugin** is not required; standalone JAR/CLI is used.

---

## Related documents

- [Specifications — Freerouting Integration](../Specifications/Freerouting_Integration.md)
- [07 — Design Audits](07_Design_Audits.md)
- [09 — Configuration Reference](09_Configuration_Reference.md)

## Parent

- [User Guides](README.md)