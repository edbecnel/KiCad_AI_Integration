# Document Metadata Standard

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Governance](README.md) › Document Metadata Standard

> **Status:** Approved
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration governed documents
> **Last Reviewed:** 2026-07-14
> **Review Frequency:** Annual
> **Authoritative:** Yes

## Purpose

This standard defines the minimum metadata required to govern engineering
documentation consistently.

## Initial Representation

Until EDF adopts a machine-readable front-matter format, metadata should be written
as a Markdown block immediately below the document title.

```markdown
> **Status:** Draft
> **Owner:** Team or role
> **Applies To:** Project, subsystem, or audience
> **Last Reviewed:** YYYY-MM-DD
> **Review Frequency:** Annual
> **Authoritative:** Yes

## Applicability

This document defines baseline governance that applies to:

- the Engineering Documentation Framework repository
- projects that adopt the Engineering Documentation Framework

EDF itself follows this baseline governance and also follows the additional
framework-specific requirements in [EDF Governance](EDF_Governance.md).

```

## Required Fields

| Field | Required | Purpose |
|---|---:|---|
| Status | Yes | Identifies the lifecycle state |
| Owner | Yes | Identifies the accountable role or group |
| Applies To | Yes | Defines scope |
| Last Reviewed | Yes for approved or maintained documents | Records the most recent substantive review |
| Review Frequency | Yes for governed documents | Defines the expected review interval |
| Authoritative | Yes for canonical candidates | Distinguishes source documents from supporting material |

## Optional Fields

| Field | Purpose |
|---|---|
| Version | Document-specific version when needed |
| Approver | Required approval authority |
| Approved On | Date approval was granted |
| Supersedes | Document replaced by this one |
| Superseded By | Replacement document |
| Related ADRs | Links to applicable decisions |
| Security Classification | Handling requirements |
| Review Notes | Context for the next review |

## Valid Status Values

- Draft
- In Review
- Approved
- Maintained
- Deprecated
- Archived

## Owner Values

The owner should normally be a stable role or team, not an individual person.

Preferred:

```text
Architecture Team
Project Maintainer
Security Owner
Documentation Owner
Engineering Documentation Framework
```

Avoid using a named individual unless the project is intentionally maintained by
one person and no stable role exists.

## Authoritative Values

Use:

- `Yes` for the canonical source of a concept
- `No` for supporting, derived, or informational content

A concept should normally have only one authoritative document.

## Review Frequency Values

Recommended values:

- Monthly
- Quarterly
- Semiannual
- Annual
- Per Release
- On Change
- Not Scheduled

`Not Scheduled` should be limited to drafts, archives, or low-risk reference material.

## Machine-Readable Future

A later EDF version may introduce YAML front matter or a repository governance
manifest. The semantic meaning defined here should remain stable even if the
serialization format changes.

## Parent

- [Governance](README.md)

## Related Documents

- [Governance Overview](Governance_Overview.md)
- [Document Lifecycle](Document_Lifecycle.md)
- [Ownership and Review](Ownership_and_Review.md)
- [Governance Analyzer Compliance](Analyzer_Compliance.md)
