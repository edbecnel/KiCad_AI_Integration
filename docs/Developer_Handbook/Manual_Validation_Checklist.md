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

Freerouting is **not bundled** with KiCad AI Integration. You install it separately; KAI invokes it as an external autorouter in headless batch mode (`-de` DSN in, `-do` SES out). See [Freerouting Integration](../Specifications/Freerouting_Integration.md).

### Two different install artifacts

**Important:** the macOS DMG and the standalone JAR are not the same thing. Pick the row that matches what you installed:

| What you installed | What it is | Does KAI find it automatically? |
| ------------------ | ---------- | --------------------------------- |
| **`freerouting.app`** from the macOS **`.dmg`** in `/Applications` | GUI app bundle with its own bundled runtime | **No** — set `freerouting_cli` (Option B) |
| **`freerouting-….jar`** from [GitHub Releases](https://github.com/freerouting/freerouting/releases) | Standalone JAR for `java -jar …` | **Only** on macOS if saved as `~/Applications/freerouting.jar`; otherwise set `freerouting_jar` (Option A) |

Installing **`freerouting.app` does not create a loose `freerouting.jar` in `/Applications`**. Any JAR inside the app bundle is embedded for the GUI launcher — not the path KAI expects. For JAR-based routing, download the platform-independent `.jar` separately (Option A).

### Requirements

| Requirement | Notes |
|-------------|--------|
| **Java 25+** (JRE or JDK) | Required for **Option A** (standalone `.jar`). Freerouting 2.2.x is built for Java 25; older Java causes `UnsupportedClassVersionError`. JDK 26 is fine. Not required for **Option B** (native CLI / `.app` bundle includes its own runtime). |
| **KiCad 8+** with **PCB Editor open** | DSN export and SES import use `pcbnew` — not `kicad-cli` |
| **Saved `.kicad_pcb`** | Beside your `.kicad_pro` |
| **`routing_enabled: true`** | Routing tab stays disabled until this is set |

### Choose one install path for KAI

KAI needs **either** `freerouting_jar` **or** `freerouting_cli` in [`~/kicad_ai_config.json`](../User_Guides/09_Configuration_Reference.md) (or the matching env var). Do not leave both unset after installing only the GUI app.

---

### Option A — Standalone JAR (recommended for manual validation)

Use this when you want explicit control over Java and the exact Freerouting version.

1. **Install Java 25 or newer** (Temurin, Oracle JDK, etc.). Verify:

   ```bash
   java -version
   ```

   You should see version **25** or higher (e.g. 26).

2. **Download the platform-independent JAR** from [freerouting/freerouting releases](https://github.com/freerouting/freerouting/releases) — the file named like `freerouting-2.2.3.jar` (not the macOS `.dmg`).

3. **Save the JAR to a stable path** (use the full path in config):

   - **macOS:** `~/Applications/freerouting.jar` — note **`~` home folder**, not `/Applications`
   - **Linux:** `~/bin/freerouting.jar`
   - **Windows:** `C:\Tools\freerouting.jar`

4. **Smoke-test** before configuring KAI:

   ```bash
   java -jar /full/path/to/freerouting.jar -h
   ```

   **Pass:** Freerouting help text; batch flags include `-de` (DSN input) and `-do` (SES output).

5. **Configure KAI** — edit `~/kicad_ai_config.json`:

   ```json
   {
     "routing_enabled": true,
     "freerouting_jar": "/Users/YOUR_USERNAME/Applications/freerouting.jar"
   }
   ```

   Replace `YOUR_USERNAME` with your macOS login name, or use the exact path from step 3.

   **Environment variable alternative:**

   ```bash
   export FREEROUTING_JAR=/Users/YOUR_USERNAME/Applications/freerouting.jar
   ```

---

### Option B — Native executable (macOS `.app`, Linux zip, Windows MSI)

Use this when you already installed **`freerouting.app`** from the DMG or another native installer. KAI calls the **binary inside the bundle**, not the Finder shortcut.

#### macOS — `freerouting.app` in `/Applications`

1. Confirm the app is installed:

   ```bash
   ls /Applications/freerouting.app/Contents/MacOS/freerouting
   ```

2. **Smoke-test** the CLI entry point (same binary KAI will invoke):

   ```bash
   /Applications/freerouting.app/Contents/MacOS/freerouting -h
   ```

   **Pass:** help text with `-de` / `-do` flags. If this fails, fix the app install before configuring KAI.

3. **Configure KAI** — edit `~/kicad_ai_config.json`:

   ```json
   {
     "routing_enabled": true,
     "freerouting_cli": "/Applications/freerouting.app/Contents/MacOS/freerouting"
   }
   ```

   **Environment variable alternative:**

   ```bash
   export FREEROUTING_CLI="/Applications/freerouting.app/Contents/MacOS/freerouting"
   ```

   Do **not** set `freerouting_jar` to a path inside `freerouting.app/Contents/…` unless you have verified that file exists and runs with your system Java. Prefer `freerouting_cli` for DMG installs.

#### Linux / Windows

1. Install per [upstream integrations](https://github.com/freerouting/freerouting/blob/master/docs/integrations.md) (e.g. unzip Linux release, or Windows MSI).
2. Note the full path to the `freerouting` executable (or ensure it is on `PATH` as `freerouting`).
3. Smoke-test: `freerouting -h` or `/full/path/to/freerouting -h`.
4. Set `freerouting_cli` in `~/kicad_ai_config.json` to that full path.

---

### Verify KAI can see Freerouting (does not run KiCad)

From the repository root:

```bash
python scripts/manual_e2e_checklist.py --check-env
```

Confirm **one** of the following is set:

- `FREEROUTING_JAR` → full path to your standalone `.jar` (Option A), **or**
- `FREEROUTING_CLI` → full path to the native binary (Option B)

For Option A, also confirm `java -version` shows 25+ and `java` is on `PATH`.

Then open KiCad → **Routing** tab (**Ctrl+7**) → status line should read **Engine: freerouting (installed)**. If it says **not installed**, the path in config/env is wrong or the smoke test in Option A/B failed.

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
| Run autoroute disabled | `routing_enabled: true`, Freerouting path set, saved `.kicad_pcb` |
| Engine not installed | Config path must be **full path** to standalone JAR (Option A) or CLI binary (Option B). Installing `freerouting.app` alone is not enough — set `freerouting_cli` to `/Applications/freerouting.app/Contents/MacOS/freerouting` |
| Installed DMG but no JAR found | Expected — DMG does not install `freerouting.jar` in `/Applications`. Use Option B (`freerouting_cli`) or download the `.jar` separately (Option A) |
| `UnsupportedClassVersionError` (JAR) | Freerouting 2.2+ needs **Java 25+**; run `java -version` and upgrade |
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
