# Workflow: PCB Layout Review and Route
[Home](../../../README.md) › [Project Index](../../../PROJECT_INDEX.md) › [User Guides](../README.md) › [Workflows](../Step_By_Step_Guides.md) › Workflow: PCB Layout Review and Route



## Overview

Review PCB layout with **Audits**, run **Freerouting** autoroute with checkpoint safety, then optionally run **post-route AI review**.

## Prerequisites

- Saved `.kicad_pcb`
- API key for audits / post-route review
- Freerouting configured (`routing_enabled`, `freerouting_jar`) for routing step

---

## Steps

### 1. Refresh context

Open Assistant → **Refresh context**.

### 2. PCB audits (Ctrl+6)

1. **Audits** tab → **PCB layout review** → approve.
2. Review findings; optionally **Explain DRC**.
3. Reports saved under `kicad_ai/reviews/`.

See [07 — Design Audits](../07_Design_Audits.md).

### 3. Autoroute (Ctrl+7)

1. **Routing** tab — confirm Freerouting installed.
2. Review **Routing policy / exclusions**.
3. **Run autoroute** → approve → wait for quality report in **Output**.

See [08 — PCB Routing](../08_PCB_Routing.md).

### 4. Accept or reject

- **Accept candidate** — promotes route to your `.kicad_pcb` (confirm).
- **Reject candidate** — discard; board unchanged.

Reload board in KiCad after accept.

### 5. Post-route review (optional)

**Post-route AI review** → approve → review findings in **Output** and `kicad_ai/reviews/`.

---

## Expected outcome

- Audit JSON reports on disk
- Routed PCB (if accepted) or unchanged board (if rejected)
- Optional post-route review report

## Parent

- [User Guides](../README.md)
