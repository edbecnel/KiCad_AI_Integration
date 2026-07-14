# AI Repository Workflow

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › AI Repository Workflow

> **Status:** Maintained
> **Owner:** Engineering Documentation Framework
> **Applies To:** AI-assisted repository analysis, documentation, and implementation work
> **Last Reviewed:** 2026-07-11
> **Review Frequency:** On Change
> **Authoritative:** Yes

## Purpose

This document defines the standard workflow for AI-assisted work on a Git-hosted engineering project.

AI assistants operate directly on the local repository working tree through an IDE such as **Cursor with Composer 2.5 (standard)** or **Visual Studio Code with GitHub Copilot**. The repository remains authoritative; changes are reviewed through Git and committed like any other engineering work.

## Guiding Principle

The local Git repository is the single source of truth.

AI assistants must read and modify files in the current working tree. They must not rely on stale conversation copies, reconstructed content, or remote repository snapshots when the local repository is available.

## Supported Environments

| Environment | Role |
|---|---|
| **Cursor + Composer 2.5 (standard)** | Primary environment for documentation and multi-file implementation |
| **Visual Studio Code + GitHub Copilot** | Primary environment for developers using VS Code |
| **VS Code + Continue + local models** | Optional for privacy-sensitive or offline work |

Browser-based AI tools that cannot access the local repository directly are not part of the standard EDF workflow.

## Responsibility Model

### AI Assistant Responsibilities

The AI assistant is responsible for:

- reading the current repository structure and relevant files from the working tree
- identifying the smallest focused set of required changes
- modifying complete files rather than supplying partial replacement fragments
- preserving repository paths and file names unless a change has been explicitly approved
- updating navigation and cross-links when documents change
- running available validation when practical
- reporting limitations, validation failures, and unresolved findings honestly

### Developer Responsibilities

The developer is responsible for:

- working in a current local clone of the repository
- reviewing the Git diff after AI-assisted changes
- running project-specific validation when needed
- accepting, revising, or rejecting the proposed changes
- committing approved changes in small, logical commits
- pushing completed work to the remote repository

The human developer remains the final authority.

## Standard Workflow

1. Open the project in Cursor (Composer 2.5 standard) or VS Code with GitHub Copilot.
2. Ensure the local repository is current (`git pull` when appropriate).
3. Identify the scope of the requested change.
4. Direct the AI assistant to read relevant files from the working tree.
5. The AI assistant modifies complete files in place.
6. Run the Framework Advisor or other applicable validation when practical.
7. The developer reviews `git status` and `git diff`.
8. The developer commits approved changes.
9. The developer pushes to the remote repository.

## Complete File Delivery

When a file changes, the AI assistant must produce the complete replacement file at its normal repository path.

The AI assistant should not require the developer to:

- copy and paste Markdown sections manually
- splice partial code fragments into existing files
- reconstruct a document from multiple response blocks
- guess where a proposed change belongs
- reformat generated content before it can be reviewed

Complete-file delivery makes the proposed repository state explicit and allows Git to show the exact diff.

## Small, Focused Changes

Each change set should address one focused implementation stage.

Do not combine unrelated work merely because several changes are available. Smaller changes provide:

- clearer Git diffs
- easier validation
- simpler rollback
- more meaningful commit history
- lower risk of accidental scope expansion
- better traceability between findings and corrections

## Review Procedure

After AI-assisted edits, the developer reviews the proposed changes:

```bash
git status
git diff
```

Run project validation before committing. For EDF self-hosting work:

```bash
bash ./scripts/run_self_hosting_validation.sh
```

After approval:

```bash
git add <changed-files>
git commit -m "Descriptive commit message"
git push
```

## Repository Safety Rules

Unless explicitly approved for a particular implementation, the AI assistant must not automatically:

- overwrite unrelated user content
- rename user files
- delete user files
- move user files
- merge documents with uncertain ownership
- include unrelated cleanup
- change generated-file permissions without documenting the change
- treat an analyzer recommendation as authorization to modify the repository

Existing files become project-owned. Generators create only missing files. Analyzers remain read-only.

## Verification

Whenever practical, the AI assistant should:

1. run or extend the Framework Advisor or other project analyzer
2. capture the relevant pre-change findings
3. implement the focused corrections
4. rerun validation
5. report measurable improvements and remaining issues

A successful command does not replace human review. The Git diff remains the definitive view of the proposed change.

## Executable Permissions

When shell scripts are added or modified, restore executable permissions if needed:

```bash
chmod +x scripts/*.sh
git update-index --chmod=+x scripts/*.sh
```

Limit these commands to the affected scripts whenever possible.

## Commit Quality

Each commit should describe the implementation outcome, not the mechanics of AI assistance.

Preferred:

```text
docs(ai): define repository-first IDE workflow
```

Avoid:

```text
update files
```

## Exceptions and Escalation

When the requested change cannot be completed safely from available repository information, the AI assistant should:

- complete all well-supported work that remains possible
- clearly identify what could not be completed
- avoid inventing repository contents
- avoid silently broadening the scope

## Parent

- [AI Engineering Handbook](README.md)

## Related Documents

- [AI Philosophy](AI_Philosophy.md)
- [AI Roles](AI_Roles.md)
- [Context Checklist](Context_Checklist.md)
- [Verification](Verification.md)
- [AI Governance](Governance.md)
- [Documentation Change Management](../Governance/Change_Management.md)
- [Document Metadata Standard](../Governance/Document_Metadata_Standard.md)
