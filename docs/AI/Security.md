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
