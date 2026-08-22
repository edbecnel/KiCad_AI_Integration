# Security

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [AI Engineering Handbook](README.md) › Security


## Purpose

This document defines security and privacy rules for using AI tools in software engineering projects.

AI usage must not compromise credentials, regulated data, private information, intellectual property, or production systems.

## No Secrets in Prompts

Never paste secrets into cloud AI tools.

This includes:

- API keys
- passwords
- private keys
- database credentials
- access tokens
- production configuration values
- customer data
- regulated data
- personally identifiable information unless explicitly approved by policy

## Use Local AI for Sensitive Context

When working with sensitive or proprietary code, prefer local AI tools when practical.

Local AI is useful for:

- private code explanation
- internal documentation
- small refactoring
- offline work
- sensitive project context

## Cloud AI Approval

Cloud AI may be appropriate for many engineering tasks, but teams should define what may and may not be shared.

Projects should document:

- approved AI tools
- approved data categories
- prohibited data categories
- model usage policies
- review requirements
- exception process

## KiCad AI Integration Security

KiCad AI Integration enforces these additional rules:

- store `ANTHROPIC_API_KEY` in environment variables — never hardcode or commit
- require explicit user approval before any cloud API transmission
- provide a context preview showing what will be sent
- support selective context inclusion via user toggles per data type
- never transmit project data automatically

See [Development Environment](../Developer_Handbook/01_Development_Environment.md) for credential setup.

## Credential storage

- **API keys:** `ANTHROPIC_API_KEY` environment variable, or optional local config (`kicad_ai_config.json` in user home — not committed)
- **Never** commit `.env`, API keys, or project-specific secrets to the repository
- The wxPython chat UI masks the API key field; loaded from env/config at dialog open

## What leaves the machine

| Action | Data transmitted | Approval gate |
|--------|------------------|---------------|
| **Chat** (`--ui-chat`) | Selected context (schematic summary, BOM, PCB, ERC/DRC, netlist, optional schematic image) + user question | Approve & Send in UI |
| **AERF stage** (`--ui-aerf`) | One stage prompt: project snapshot, KB excerpt, prior stage JSON, EKM excerpts | Per-stage Approve & Send |
| **Datasheet HTTPS fetch** | URL only (server response is PDF stored locally) | Automatic on resolve; user controls symbol fields |
| **AI datasheet discovery** | Part value + provider web search query | Opt-in; URL approval before download unless auto-fetch enabled |
| **SUBCKT generation** | Symbol context + datasheet text (Tier A) | User initiates from Simulation panel |
| **`--ask` CLI** | Same as chat without UI preview | **Dev bypass — no approval** |

Datasheet PDFs and generated SPICE libraries remain in `~/kicad_ai_library/` and project `kicad_ai/` unless explicitly included in a prompt (e.g. Tier A PDF text extraction).

## Security Review

AI-generated changes require extra care when they affect:

- authentication
- authorization
- encryption
- input validation
- database access
- file handling
- network communication
- deployment configuration
- secrets management
- audit logging

## Documentation Security

Documentation should never expose secrets.

Deployment and environment documentation may list variable names, but not secret values.

Example acceptable documentation:

```text
DATABASE_URL must be configured in the deployment environment.
```

Example unacceptable documentation:

```text
DATABASE_URL=postgres://user:password@example.com/db
```

## Related Documents

- [Governance.md](./Governance.md)
- [Verification.md](./Verification.md)
- [AI_Decision_Matrix.md](./AI_Decision_Matrix.md)

## Parent

- [AI Engineering Handbook](README.md)
