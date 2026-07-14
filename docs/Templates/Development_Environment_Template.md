# Development Environment

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](../Developer_Handbook/README.md) › Development Environment

## Purpose

**Required**

Describe how developers set up, configure, and maintain a local development environment that matches production closely enough to build and test software confidently.

New contributors should begin with [00_First_Time_Setup.md](../Developer_Handbook/00_First_Time_Setup.md), which links to the sections below.

## When to use it

**Required**

- Onboarding new contributors
- Updating toolchain or dependency versions
- Diagnosing "works on my machine" issues
- Aligning local tooling with CI

---

## Prerequisites

**Required**

### Required software

| Tool | Minimum version | Purpose | Install reference |
|------|-----------------|---------|-------------------|
| [Tool] | [Version] | [Purpose] | [Link or command] |

### Optional tools

**Optional**

- [Tool and when it helps]

### Hardware recommendations

**Optional**

- [RAM, disk, OS notes if relevant]

---

## Repository setup

**Required**

### Clone and initialize

```bash
git clone <repository-url>
cd <project-directory>
# [project-specific setup command]
```

### Environment variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| [NAME] | Yes/No | [Description] | [Example] |

### Secrets handling

- Store secrets in `.env` (gitignored) or a team secret manager.
- Provide `.env.example` with variable names and dummy values.
- Never commit credentials, tokens, or private keys.

---

## Local services

**Required** when the project uses local databases, caches, or containers.

### Running dependencies

[How to start databases, caches, message queues, or mock services.]

### Service endpoints (local)

| Service | URL | Notes |
|---------|-----|-------|
| [Service] | [URL] | [Notes] |

### Seed data

[How to load fixtures, migrations, or sample data.]

---

## Running the application

**Required**

### Start commands

```bash
# [Development server command]
```

### Verify installation

```bash
# [Health check or smoke test]
```

### Common development tasks

| Task | Command |
|------|---------|
| Install dependencies | [command] |
| Run linter | [command] |
| Run formatter | [command] |
| Run tests | [command] |
| Build production artifact | [command] |

---

## IDE configuration

**Optional**

### Recommended extensions

- [Extension — purpose]

### Editor settings

[Point to `.editorconfig`, `.vscode/settings.json`, or equivalent.]

### AI tooling

[Link to project AI conventions and `docs/AI/`.]

---

## Troubleshooting

**Optional**

### Issue: [Common problem]

**Symptoms:** [What the developer sees]

**Resolution:**

1. [Step]

### Getting help

- [PROJECT_INDEX.md](../../PROJECT_INDEX.md)
- [Team channel or escalation path]

## Parent

- [Developer Handbook](../Developer_Handbook/README.md)

## Related documents

- [00_First_Time_Setup.md](../Developer_Handbook/00_First_Time_Setup.md)
- [Database](../Database/)
- [Deployment](../Deployment/)
