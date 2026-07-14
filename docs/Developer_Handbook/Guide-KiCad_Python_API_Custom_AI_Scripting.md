# Guide: KiCad Python API + Custom AI Scripting for Circuit Review

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](README.md) › KiCad Python API Scripting

> **Status:** Draft
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration developers
> **Authoritative:** No

### Guide: KiCad Python API + Custom AI Scripting for Circuit Review

When working with an open-source toolchain, general LLMs (like Claude 3.5 Sonnet) struggle to analyze an entire raw PCB layout file due to noise, formatting, and file size. However, KiCad features a robust, fully exposed Python scripting API (`pcbnew`).

By writing small Python scripts, you can programmatically extract structural layout data—such as high-current loop path lengths, trace widths, and critical isolation gaps—and format them into clean, structured data structures (JSON/YAML) that an AI can review perfectly.

---

### 1. Setting Up the Environment

KiCad bundles its own Python interpreter. To run custom scripts that interface with your board layout, you must use KiCad's internal Python shell or execute them via the integrated scripting console.

### Accessing the KiCad Scripting Console:

1. Open your project board layout in **KiCad PCB Editor (`pcbnew`)**.
2. Go to the top menu and select **Tools > Scripting Console**.
3. This opens an interactive Python environment pre-loaded with KiCad's internal layout objects.

---

### 2. Structural Data Extraction Scripts

Below are custom Python scripts you can generate using an AI or run directly to extract critical structural data from your Bedini/Babcock flyback driver board.

### Script A: Extracting Trace Widths and Lengths for High-Current Flyback Loops

Because John Bedini and Paul Babcock's switching circuits handle sharp, high-voltage inductive spikes, narrow traces can vaporize or create unwanted parasitic inductance. This script isolates high-power nets (like your coil and battery return paths) and extracts their physical trace properties.

python

```
import pcbnew

def extract_power_net_properties():
    # Load the currently open board in the editor
    board = pcbnew.GetBoard()
    
    # Define the critical high-current nets you want to audit
    target_nets = ["HV_Flyback", "Coil_Plus", "Coil_Minus", "GND_Power", "Battery_Charge"]
    extracted_data = {}

    print("--- START AI DATA EXTRACT ---")
    for track in board.GetTracks():
        net_name = track.GetNetname()
        
        if net_name in target_nets:
            if net_name not in extracted_data:
                extracted_data[net_name] = []
                
            # Convert internal KiCad units (nanometers) to millimeters
            width_mm = track.GetWidth() / 1000000.0
            length_mm = track.GetLength() / 1000000.0
            layer = board.GetLayerName(track.GetLayer())
            
            extracted_data[net_name].append({
                "layer": layer,
                "width_mm": round(width_mm, 3),
                "length_mm": round(length_mm, 3)
            })
            
    # Format cleanly as pseudo-JSON for easy copy-pasting to the AI
    import json
    print(json.dumps(extracted_data, indent=2))
    print("--- END AI DATA EXTRACT ---")

# Run the function
extract_power_net_properties()
```

Use code with caution.

### Script B: Verifying Electrical Clearance (Isolation Barriers)

For a Raspberry Pi Pico PLC to safely control a high-voltage inductive matrix, there must be strict physical isolation. This script pulls out the exact mechanical distance between your low-voltage microcontroller pins and your high-voltage switching nets to check for creepage and clearance violations.

python

```
import pcbnew

def audit_clearance_boundaries():
    board = pcbnew.GetBoard()
    
    print("--- START AI ISOLATION BOUNDARY EXTRACT ---")
    # Pull net class rules defined in your KiCad project
    netclasses = board.GetDesignSettings().GetNetClasses()
    
    for name, netclass in netclasses.items():
        print(f"NetClass: {name}")
        print(f"  - Target Clearance Rule: {netclass.GetClearance() / 1000000.0} mm")
        print(f"  - Target Trace Width: {netclass.GetTrackWidth() / 1000000.0} mm")
        
    print("\nComponent Grouping for Air-Gap Verification:")
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        # Look specifically for isolation components like Optocouplers or Gate Drivers
        if "U" in ref or "ISO" in ref:
            print(f"Component: {ref} ({footprint.GetValue()})")
            print(f"  - Position X/Y: {footprint.GetPosition().x / 1000000.0}, {footprint.GetPosition().y / 1000000.0}")
            
    print("--- END AI DATA EXTRACT ---")

audit_clearance_boundaries()
```

Use code with caution.

---

### 3. Feeding Extracted Data into the AI Model

Once you execute these scripts inside the KiCad Scripting Console, copy the clean text printed between the `--- START AI DATA EXTRACT ---` tags and feed it directly into Claude 3.5 Sonnet along with your schematic image.

### Recommended Prompt for Analyzing Python API Data:

text

```
[Upload High-Resolution Schematic Image]

Act as an expert power electronics PCB layout engineer specializing in high-dV/dt electromagnetic switching circuits. I am building a John Bedini / Paul Babcock high-efficiency inductive energy harvesting circuit controlled by a Raspberry Pi Pico PLC. 

I have extracted geometric and structural board routing data using the KiCad Python API. Please cross-reference this Python data against the attached visual schematic.

<kicad_python_extracted_data>
[PASTE THE JSON/TEXT OUTPUT FROM SCRIPT A & B HERE]
</kicad_python_extracted_data>

Analyze the data for the following specific physical hardware vulnerabilities:
1. TRACE EM CAPACITY & PARASITICS: Review the trace widths for the 'HV_Flyback' and 'Coil' nets. Given high-frequency, steep inductive transients, are the trace widths sufficient to minimize trace resistance and parasitic inductance?
2. CREEPAGE & CLEARANCE AUDIT: Review the clearance parameters and positions of my isolation devices. Is the gap between the Raspberry Pi Pico logic nets and the high-voltage flyback recapture loop physically safe to prevent catastrophic arc-over or digital noise injection?
3. DESIGN FOR EXTREMES: Identify any areas where trace lengths on high-current switching paths are too long, which could lead to unwanted ringing or radiative EMI that might crash the Pico PLC.
```

Use code with caution.

---

### 4. Best Practices for This Workflow

- **Label Your Nets in KiCad First**: The Python API pulls data based on Net Names. Instead of leaving default names like `Net-(D1-Pad2)`, use global or local labels in your KiCad schematic (e.g., `PICO_GPIO15`, `FLYBACK_NODE`, `BAT_RETURN`) so the extracted data remains highly human- and AI-readable.
- **Iterative Scripting via Claude**: If you need to find something highly specific—such as locating all decoupling capacitors and calculating their physical distance to the Raspberry Pi Pico's power pins—ask Claude to write a custom `pcbnew` Python script for you first, run it in KiCad, and then give the result back to Claude for analysis.