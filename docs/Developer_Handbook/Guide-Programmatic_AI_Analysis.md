# Guide: Programmatic AI Analysis via KiCad Python Scripting

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](README.md) › Programmatic AI Analysis

> **Status:** Draft
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration developers
> **Authoritative:** No

### Guide: Programmatic AI Analysis via KiCad Python Scripting

When optimizing advanced switching matrices like a **Bedini/Babcock flyback recovery system**, manual text dumping can introduce formatting human errors. Because KiCad saves schematics (`.kicad_sch`) and PCBs (`.kicad_pcb`) as plain text **S-expressions**, you can use Python to parse, extract, and clean hardware metadata automatically.

This guide details how to build an automated python preprocessing layer that pipes clean JSON/structured telemetry out of KiCad directly into a frontier LLM prompt window.

---

### 1. Automated Architecture Pipeline

Instead of pasting unorganized text files into an AI, use Python to aggregate your design intent into an optimized, highly dense data bundle.

```
+------------------+     (Python Script)     +--------------------+

|  KiCad Files     | ----------------------> | AI Data Pre-Filter |
|  - S-Expressions |                         |  - Component JSON  |
|  - Netlist Data  |                         |  - Net Loop Map    |
+------------------+                         +--------------------+
                                                        |
                                                        v
+------------------+     (System Prompt)     +--------------------+

| Claude 3.5 API / | <---------------------- | Structured Prompt  |
| Web App Analysis |                         |  - Target Audits   |
+------------------+                         +--------------------+
```

---

### 2. Step 1: Writing the KiCad Data Extractor Script

Because KiCad 8+ utilizes structured S-expressions, native script execution allows you to extract precise trace metadata or isolate specific sensitive nodes (like your Raspberry Pi Pico's switching tracks and your primary flyback coil loop) without cluttering the AI's window with unrelated ground planes.

Save the following Python script as `kicad_ai_prep.py` in your local project folder:

python

```
import os
import json
import re

def extract_critical_nets(netlist_path):
    """
    Parses a SPICE/KiCad netlist to isolate component pins connected 
    to critical switching loops and control boundaries.
    """
    with open(netlist_path, 'r') as f:
        lines = f.readlines()
        
    net_map = {}
    current_net = None
    
    # Basic structural pass for custom grouping
    for line in lines:
        line = line.strip()
        if not line or line.startswith('*'):
            continue
        # Catch standard net definitions or component lines depending on format
        # This example builds a lightweight component connection registry
        parts = line.split()
        if len(parts) >= 3:
            ref = parts[0]
            # Map references to active loops
            if any(prefix in ref for prefix in ['Q', 'D', 'U', 'L']):
                net_map[ref] = parts[1:]
                
    return net_map

def generate_ai_payload(project_name, description_text, netlist_file):
    """
    Assembles the data payload to copy-paste cleanly or send to an API.
    """
    net_data = extract_critical_nets(netlist_file)
    
    payload = {
        "project": project_name,
        "critical_nodes": net_data,
        "design_constraints": description_text
    }
    
    output_path = f"{project_name}_ai_input.json"
    with open(output_path, 'w') as out:
        json.dump(payload, out, indent=2)
    
    print(f"[SUCCESS] AI-optimized hardware telemetry exported to {output_path}")

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    # Define variables matching your Bedini/Babcock system setup
    PROJECT = "Bedini_Babcock_Pico_Driver"
    DESCRIPTION = (
        "High-voltage flyback recovery system. Raspberry Pi Pico controls pulse-width timing "
        "of inductive coil discharges to feed back into battery storage. Target isolation "
        "must hold at 400V transients. Switching frequency runs up to 25kHz."
    )
    NETLIST = "project_netlist.net" # Generate via KiCad: File > Export > Netlist
    
    if os.path.exists(NETLIST):
        generate_ai_payload(PROJECT, DESCRIPTION, NETLIST)
    else:
        print(f"[ERROR] Could not locate netlist file at: {NETLIST}. Please export from KiCad first.")
```

Use code with caution.

---

### 3. Step 2: The Structured Engineering Prompt Template

Once your Python script generates the filtered JSON data bundle, you can upload or paste the output file directly into Claude 3.5 Sonnet alongside your visual circuit schematics. Use the system template below to force the model to behave like an embedded power-electronics review compiler.

text

```
[Upload High-Resolution Schematic Image]
[Upload the generated Bedini_Babcock_Pico_Driver_ai_input.json file]

SYSTEM ROLE: Act as a Principal Power Electronics Hardware Safety Audit Engine. You are analyzing an open-source hardware project running an un-clamped inductive flyback recovery matrix.

Please ingest the attached high-resolution schematic image along with the filtered Python JSON dataset representing our KiCad connectivity graph. 

Execute a strict, sequential security review addressing the items below:

1. ISOLATION BARRIER INTELLIGENCE:
   Cross-reference the component pins assigned to the Raspberry Pi Pico (U1/Pico markers) in the JSON data against the visual schematic. Confirm if any direct, non-isolated path exists between the Pico's 3.3V GPIO pins and the high-voltage collector/drain switching loops of the recovery transistors. Flag missing optocouplers or isolated gate drivers immediately.

2. INDUCTIVE FLYBACK ROUTING VALIDATION:
   Scan the visual schematic tracking outward from the inductive coil pins. Verify that the recovery diodes (D) are oriented to block forward power when the primary switch is ON, and fully forward-biased toward the output battery pack during the inductive flyback event (Switch OFF). Cross-check this layout logic with the 'critical_nodes' map in the JSON file.

3. REPETITIVE TRANSIENT RISK EVALUATION:
   Based on the switching parameters provided in the JSON 'design_constraints' block, flag whether the physical placement of snubbers, TVS arrays, or fast-recovery steering diodes are structurally close enough to the switching transistors to prevent localized avalanche breakdown.
```

Use code with caution.

---

### 4. Automation Refinement Strategies

- **BOM Attribute Extraction**: You can update the script to pull customized `Datasheet` or `Vds_max` custom fields directly out of your KiCad `.kicad_sch` file strings. Passing specific part voltage tolerances allows the AI model to check your active circuit parameters directly against structural silicon real-world limits.
    
- **Firmware Context Insertion**: Append an automation line to pull your raw `main.py` or `timing.c` files into the text array. This allows the AI to dynamically check if your dead-time logic calculations correctly match the turn-off latency specified inside your hardware transistor datasheets.