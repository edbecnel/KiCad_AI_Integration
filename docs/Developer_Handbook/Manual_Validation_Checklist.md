# Manual Validation Checklist

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](README.md) › Manual Validation

> **Status:** Maintained  
> **Owner:** Project maintainers  
> **Applies To:** Phase 1 manual E2E and Freerouting validation

## Phase 1 — KiCad chat E2E

1. Open KiCad PCB Editor with a saved `.kicad_pro` project.
2. Launch **Tools → External Plugins → KiCad AI Assistant** (or Scripting Console).
3. Click **Refresh context** on the Assistant shell.
4. Open **Chat** tab, select a template, enter an engineering question.
5. Click **Approve & Send** and confirm a context-aware response without manual export/copy-paste.

**Pass criteria:** Response references project symbols/nets from the active design.

## Freerouting routing E2E

**Prerequisites:**

- `routing_enabled: true` in config
- `freerouting_jar` or `FREEROUTING_JAR` set
- Open `.kicad_pcb` in PCB Editor (pcbnew required for DSN/SES)

**Steps:**

1. Open **Routing** tab (Ctrl+7).
2. **Generate policy from AI** or use a saved `kicad_ai/routing_policy.json`.
3. **Run autoroute** → approve → wait for checkpoint candidate.
4. Review quality report; optional **Post-route AI review**.
5. **Compare candidates** after multiple runs; **Re-route with policy** to iterate.
6. **Accept candidate** or **Reject candidate**.

**Automated helper (env check only):**

```bash
python scripts/manual_e2e_checklist.py --check-env
FREEROUTING_JAR=/path/to/freerouting.jar pytest -m kicad tests/integration/test_routing_e2e.py
```

## Bedini / flyback reference

1. Open `examples/minimal_blocking_oscillator/blocking_oscillator.kicad_pro`.
2. Run **Audits → Flyback recovery** or Chat template **Flyback recovery**.
3. Verify response discusses isolation, switching paths, and net labels.

See [examples/bedini_babcock/README.md](../../examples/bedini_babcock/README.md).

## Parent

- [Developer Handbook](README.md)
