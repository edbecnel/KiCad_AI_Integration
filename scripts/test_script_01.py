import sys
sys.path.insert(0, "/Users/edbecnel/Development/GitHub/KiCad_AI_Integration/src")

from ui.launcher import show_missing_datasheets_dialog

project = "/Users/edbecnel/Development/Local/kicad_test_projects/Babcock-Patent-Driver-PCB-4p/Babcock-Patent-Driver-PCB-4p.kicad_pro"

# Modal dialog; process exits after Close (no MainLoop — KiCad owns the loop when embedded).
show_missing_datasheets_dialog(project)