import sys

sys.path.insert(0, "/Users/edbecnel/Development/GitHub/KiCad_AI_Integration/src")

from ui.launcher import show_assistant_shell

project = "/Users/edbecnel/Development/Local/kicad_test_projects/Babcock-Patent-Driver-PCB-4p/Babcock-Patent-Driver-PCB-4p.kicad_pro"

show_assistant_shell(project, focus_tab="datasheets")
