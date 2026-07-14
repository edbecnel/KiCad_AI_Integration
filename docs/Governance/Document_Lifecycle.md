# Document Lifecycle

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Governance](README.md) › Document Lifecycle

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

This document defines the lifecycle states used to manage engineering documentation.

## Lifecycle States

### Draft

The document is incomplete, provisional, or actively being authored.

Draft documents:

- may contain unresolved questions
- are not authoritative
- should not be relied upon for production decisions

### In Review

The document is ready for substantive review.

Review should confirm:

- factual accuracy
- architectural consistency
- link integrity
- ownership
- scope
- approval requirements

### Approved

The document has received the required approval and may be treated as authoritative.

Approval does not mean the document is permanently complete.

### Maintained

The document is approved, actively used, and subject to ongoing review.

Canonical documents should normally be in the Maintained state.

### Deprecated

The document should no longer guide new work but remains available for transition,
history, or compatibility.

Deprecated documents must identify:

- the reason for deprecation
- the replacement document, when one exists
- the effective date

### Archived

The document is retained for historical or compliance purposes and is removed from
normal project navigation.

Archived documents must not be treated as current guidance.

## Allowed Transitions

```text
Draft → In Review
In Review → Draft
In Review → Approved
Approved → Maintained
Maintained → In Review
Maintained → Deprecated
Deprecated → Maintained
Deprecated → Archived
```

Direct transitions may be used for low-risk documentation when governance policy permits.

## Canonical Document Rule

A document must not be marked authoritative while its status is Draft or Archived.

## Deprecation Rule

A deprecated authoritative document should identify a replacement or explicitly state
that no replacement exists.

## Archive Rule

Archiving must not delete project history. Moving files may be performed only through
an explicit human-approved change.

## Parent

- [Governance](README.md)

## Related Documents

- [Governance Overview](Governance_Overview.md)
- [Document Metadata Standard](Document_Metadata_Standard.md)
- [Ownership and Review](Ownership_and_Review.md)
- [Documentation Change Management](Change_Management.md)
