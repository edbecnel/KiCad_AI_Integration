# Documentation Templates

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › Templates


## Purpose

This directory contains reusable templates for documents created under the Engineering Documentation Framework.

Templates provide a consistent starting point. They are not rigid forms. Remove optional sections that do not apply, but preserve required sections unless there is a documented reason not to.

## Template Selection Guide

| Template | Use When |
|---|---|
| `ADR_Template.md` | Recording a significant architecture decision |
| `Architecture_Document_Template.md` | Describing a system, subsystem, service, or major technical design |
| `Feature_Specification_Template.md` | Defining a feature before implementation |
| `API_Specification_Template.md` | Documenting an API or service contract |
| `Database_Design_Template.md` | Describing schemas, entities, migrations, and persistence decisions |
| `Developer_Guide_Template.md` | Explaining setup, workflows, debugging, or contributor practices |
| `Development_Environment_Template.md` | Documenting local development environment setup |
| `First_Time_Setup_Template.md` | Creating a first-time onboarding path that links to authoritative setup sections |
| `User_Guide_Template.md` | Explaining how end users perform tasks |
| `Project_Charter_Template.md` | Defining project mission, scope, goals, and constraints |
| `Project_Index_Template.md` | Creating the primary documentation hub for humans and AI assistants |
| `Project_README_Template.md` | Creating the public-facing project overview |
| `Handover_Template.md` | Transferring work between people, teams, AI sessions, or tools |
| `Release_Notes_Template.md` | Documenting a software or framework release |

## Required and Optional Sections

Templates label sections as:

- **Required** — normally retained and completed.
- **Optional** — retained only when relevant.
- **Conditional** — required when a stated condition applies.

Do not leave instructional placeholder text in finalized documents.

## Naming

Copy a template and rename the copy to describe the actual document.

Examples:

```text
ADR-0001-Use_PostgreSQL.md
Recipe_Import_Feature_Specification.md
Public_API_Specification.md
Database_Architecture.md
```

Do not modify the original template when creating project documentation.

## GitHub and Obsidian links

Follow link conventions in [Engineering Documentation Framework](../../ENGINEERING_DOCUMENTATION_FRAMEWORK.md):

- **Dual links** (Markdown + wikilink) for same-file sections and cross-file section links.
- **Markdown only** for whole-document links unless Obsidian backlinks are specifically desired.

## Cross-References

New authoritative documents should be linked from:

- `PROJECT_INDEX.md`
- the relevant domain `README.md`
- related specifications, ADRs, or guides

Prefer relative Markdown links.

## Maintenance

Templates should evolve when repeated documentation problems are discovered. Avoid creating near-duplicate templates when an existing template can be improved.

## Parent

- [Project Index](../../PROJECT_INDEX.md)

## Related Documents

- [Engineering Documentation Framework](../../ENGINEERING_DOCUMENTATION_FRAMEWORK.md)
- [Governance](../Governance/README.md)
- [AI Engineering Handbook](../AI/README.md)
