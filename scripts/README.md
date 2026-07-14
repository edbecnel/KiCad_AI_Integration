# Scripts

[Home](../README.md) · [Project Index](../PROJECT_INDEX.md)

## Purpose

Utility scripts for KiCad AI Integration, including local EDF conformance validation.

## EDF Conformance Validation

Run Framework Advisor analysis from the repository root:

```bash
./scripts/analyze_project_structure.sh .
```

Save a timestamped conformance report under `reports/conformance/`:

```bash
./scripts/run_conformance_validation.sh .
```

Reports are written to:

```text
reports/conformance/framework-advisor-YYYYMMDD-HHMMSS.txt
```

These scripts are copied from the [Engineering Documentation Framework](https://github.com/edbecnel/Engineering-Documentation-Framework). They are read-only and never modify project files.

## Setup

Ensure scripts are executable:

```bash
chmod +x scripts/*.sh
```

## Related Documents

- [Engineering Documentation Framework](../ENGINEERING_DOCUMENTATION_FRAMEWORK.md)
- [Governance Checklist](../docs/Governance/Governance_Checklist.md)
