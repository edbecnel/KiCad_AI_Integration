# Developer Handbook

[Home](../../README.md) · [Project Index](../../PROJECT_INDEX.md)

> **Documentation path:** [Project Index](../../PROJECT_INDEX.md) → Developer Handbook

## Purpose

Day-to-day project engineering: first-time setup, development environment, KiCad integration guides, Git workflow, coding standards, testing, and releases.

## Start here

New contributors begin with [00_First_Time_Setup.md](./00_First_Time_Setup.md).

## Authoritative Documents

- [00_First_Time_Setup.md](./00_First_Time_Setup.md)
- [01_Development_Environment.md](./01_Development_Environment.md)
- [02_AI_Development.md](./02_AI_Development.md)
- [05_Testing.md](./05_Testing.md)
- [KiCad Python API Scripting Guide](Guide-KiCad_Python_API_Custom_AI_Scripting.md)
- [Programmatic AI Analysis Guide](Guide-Programmatic_AI_Analysis.md)
- [In-KiCad Claude Chat Integration Guide](Guide-In_KiCad_Claude_Chat_Integration.md)
- [AI Engineering Handbook](../AI/README.md)

## Navigation

- [Project Index](../../PROJECT_INDEX.md)
- [Software Architecture (KiCad Host)](../Architecture/KiCad_AI_Integration_Software_Architecture.md)
- [Platform Architecture](../Architecture/Platform_Architecture.md)
- [Master Task List](../../tasks/MASTER_TASK_LIST.md)

## Platform import boundaries

Platform modules (`providers/`, `prompts/`, `platform_core/`, `ekm/`, `reasoning/`, `inference/`) **must not** import KiCad-specific parsers (`context/schematic_*`, `context/pcb_*`), wxPython UI, or `pcbnew`. Host modules (`context/` KiCad I/O, `ui/`, `plugin/`) may import platform modules. See [Platform Architecture](../Architecture/Platform_Architecture.md).

## Maintenance

Update this index whenever a major document in this domain is created, moved, renamed, or retired.
