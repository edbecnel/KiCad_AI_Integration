# Ownership and Review

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Governance](README.md) › Ownership and Review

> **Status:** Approved
> **Owner:** Project maintainers
> **Applies To:** Governed documentation
> **Last Reviewed:** 2026-07-14
> **Review Frequency:** Annual
> **Authoritative:** Yes

## Applicability

This document defines baseline governance that applies to:

- the Engineering Documentation Framework repository
- projects that adopt the Engineering Documentation Framework

EDF itself follows this baseline governance and also follows the additional
framework-specific requirements in [EDF Governance](EDF_Governance.md).

## Purpose

This policy defines accountability for documentation and establishes review expectations.

## Ownership Responsibilities

The document owner is accountable for:

- maintaining factual accuracy
- ensuring the document remains discoverable
- initiating required reviews
- resolving conflicting authoritative sources
- approving or obtaining approval for deprecation
- ensuring links and relationships remain valid

Ownership does not require the owner to author every change.

## Preferred Ownership Model

Use stable roles or teams whenever possible.

Examples:

- Project Maintainer
- Architecture Owner
- API Owner
- Database Owner
- Security Owner
- Operations Owner
- Documentation Owner

## Review Frequency Guidance

| Document Type | Suggested Frequency |
|---|---|
| Security policy | Quarterly or On Change |
| Deployment or operations guide | Quarterly |
| API specification | Per Release or On Change |
| Architecture document | Semiannual or On Change |
| Developer guide | Semiannual |
| User guide | Per Release |
| Project charter | Annual |
| Archived document | Not Scheduled |

Projects may choose stricter intervals.

## Review Outcomes

A review should result in one of the following:

- confirmed current
- updated
- returned to Draft
- marked Deprecated
- archived through an approved change

## Overdue Reviews

A review is overdue when:

```text
Last Reviewed + Review Frequency < Current Date
```

The Framework Advisor should report overdue reviews as recommendations and identify
the responsible owner.

## Approval Requirements

Projects should define approval requirements based on risk.

Human approval should be mandatory for:

- architectural decisions
- security policies
- production procedures
- governance policies
- destructive migration guidance
- legal or compliance documentation

## Missing Owners

A governed document without an owner is noncompliant.

The analyzer should recommend an owner category but must not invent or assign one
without project approval.

## Parent

- [Governance](README.md)

## Related Documents

- [Governance Overview](Governance_Overview.md)
- [Document Metadata Standard](Document_Metadata_Standard.md)
- [Document Lifecycle](Document_Lifecycle.md)
- [Governance Checklist](Governance_Checklist.md)
