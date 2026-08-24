# Manual Validation Checklist

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](README.md) › Manual Validation

> **Status:** Maintained  
> **Owner:** Project maintainers  
> **Applies To:** Phase 1 manual E2E and Freerouting validation  
> **Human-only:** This checklist requires KiCad and (optionally) Freerouting on your machine. An agent cannot sign off on your behalf.

## Sign-off record

Complete the sections below in KiCad, then check boxes and fill in the table.

| Item | Pass `[ ]` | Tester | Date | Notes |
|------|------------|--------|------|-------|
| Phase 1 — KiCad chat E2E | | | | |
| Freerouting routing E2E | | | | |
| Bedini / flyback reference (optional) | | | | |

When Phase 1 chat and Freerouting rows pass, check off the matching items in [`MASTER_TASK_LIST.md`](../../tasks/MASTER_TASK_LIST.md) **§1.6 Manual E2E validation** (chat + Freerouting subsections).

---

## Phase 1 — KiCad chat E2E

- [ ] Open KiCad PCB Editor with a saved `.kicad_pro` project.
- [ ] Launch **Tools → External Plugins → KiCad AI Assistant** (or Scripting Console).
- [ ] Click **Refresh context** on the Assistant shell.
- [ ] Open **Chat** tab, select a template, enter an engineering question.
- [ ] Click **Approve & Send** and confirm a context-aware response without manual export/copy-paste.

**Pass criteria:** Response references project symbols/nets from the active design.

---

## Install Freerouting

Freerouting is **not bundled** with KiCad AI Integration. You install it separately; KAI invokes it as an external autorouter ([Freerouting Integration](../Specifications/Freerouting_Integration.md)).

### Requirements

| Requirement | Notes |
|-------------|--------|
| **Java 11+** | Required if using the `.jar` distribution (`java -version`) |
| **KiCad 8+** with **PCB Editor open** | DSN export and SES import use `pcbnew` — not `kicad-cli` |
| **Saved `.kicad_pcb`** | Beside your `.kicad_pro` |

### Option A — JAR (recommended for manual validation)

1. Download the latest release from [freerouting/freerouting releases](https://github.com/freerouting/freerouting/releases) (e.g. `freerouting-…-jar-with-dependencies.jar`).
2. Place the file somewhere stable, e.g. `~/Applications/freerouting.jar` (macOS) or `~/bin/freerouting.jar`.
3. Verify Java can run it:

```bash
java -jar /path/to/freerouting.jar -h
```

You should see Freerouting help text (batch flags include `-de` for DSN input and `-do` for SES output).

### Option B — Native CLI executable

Some platforms ship a native `freerouting` executable. If you use it:

1. Install per [upstream integrations](https://github.com/freerouting/freerouting/blob/master/docs/integrations.md).
2. Ensure the binary is on `PATH` or note its full path for config.

### Configure KiCad AI Integration

Edit `~/kicad_ai_config.json` (see [Configuration Reference](../User_Guides/09_Configuration_Reference.md)):

```json
{
  "routing_enabled": true,
  "freerouting_jar": "/full/path/to/freerouting.jar"
}
```

Or use a native CLI instead of JAR:

```json
{
  "routing_enabled": true,
  "freerouting_cli": "/full/path/to/freerouting"
}
```

**Environment variables** (alternative to config file):

```bash
export FREEROUTING_JAR=/path/to/freerouting.jar
# or
export FREEROUTING_CLI=/path/to/freerouting
```

### Verify detection (does not run KiCad)

From the repository root:

```bash
python scripts/manual_e2e_checklist.py --check-env
```

Confirm `FREEROUTING_JAR` or `FREEROUTING_CLI` is set and `java` is on PATH when using the JAR.

---

## Freerouting routing E2E

**Prerequisites:**

- Freerouting installed and configured (see [Install Freerouting](#install-freerouting))
- `routing_enabled: true` in `~/kicad_ai_config.json`
- KiCad **PCB Editor** open with your project's `.kicad_pcb` loaded and saved
- Footprints placed; board ready for autorouting (partially or fully unrouted is fine)

**Steps:**

- [ ] Launch the Assistant shell from PCB Editor (**Tools → External Plugins → KiCad AI Assistant**).
- [ ] Click **Refresh context**.
- [ ] Open **Routing** tab (**Ctrl+7**).
- [ ] Confirm status shows **Engine: freerouting (installed)** (not "not installed").
- [ ] Review **Routing policy / exclusions** (or **Generate policy from AI**).
- [ ] Click **Run autoroute** → approve the dialog → wait for completion.
- [ ] Review the **Output** quality report (routed %, vias, DRC summary).
- [ ] Optional: **Post-route AI review** (requires API key).
- [ ] Optional: run autoroute again, then **Compare candidates** and **Re-route with policy**.
- [ ] **Accept candidate** (promotes route to authoritative `.kicad_pcb`) or **Reject candidate** (discards checkpoint).

**Pass criteria:**

- Autoroute completes without "Freerouting not found" or DSN/SES errors.
- Quality report shows routed metrics; Accept/Reject behaves as expected.
- Authoritative `.kicad_pcb` changes only after **Accept candidate**.

**Troubleshooting:**

| Symptom | Check |
|---------|--------|
| Run autoroute disabled | `routing_enabled`, Freerouting path, saved `.kicad_pcb` |
| Engine not installed | Config path, `manual_e2e_checklist.py --check-env`, Java for JAR |
| DSN/SES failed | Run from **inside** PCB Editor (pcbnew required) |
| Timeout | Increase `routing_timeout_sec` in config (default 600s) |

See also [08 — PCB Routing](../User_Guides/08_PCB_Routing.md) and [11 — Troubleshooting](../User_Guides/11_Troubleshooting.md).

**Optional automated pytest** (developer/CI — not a substitute for manual sign-off):

```bash
FREEROUTING_JAR=/path/to/freerouting.jar pytest -m kicad tests/integration/test_routing_e2e.py
```

---

## Bedini / flyback reference

- [ ] Open `examples/minimal_blocking_oscillator/blocking_oscillator.kicad_pro`.
- [ ] Run **Audits → Flyback recovery** or Chat template **Flyback recovery**.
- [ ] Verify response discusses isolation, switching paths, and net labels.

See [examples/bedini_babcock/README.md](../../examples/bedini_babcock/README.md) and [design_intent.md](../../examples/bedini_babcock/design_intent.md).

## Parent

- [Developer Handbook](README.md)
