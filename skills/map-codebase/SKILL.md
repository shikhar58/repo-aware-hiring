---
name: map-codebase
description: Understand the whole codebase before any hiring work. Runs a deterministic inventory, then investigates and writes hiring/_repo/codebase-map.md covering every component and service, data stores and schema, APIs, authentication and security, CI/CD pipelines, deployment and infrastructure, observability, testing, dependencies, conventions and risks, each backed by file paths. Other skills require this map. In a multi-repo workspace it maps each repo at its tier (a full map for primary repos, a shorter service card for supporting ones). Use first, when no current map exists, when check_map.py fails, or when the user asks how the codebase works.
---

# Map the Codebase

Every other skill (planning, job descriptions, rubric, screening, interview kits) depends on understanding the
system. This skill builds that understanding **once per repository**, writes it down with evidence, and keeps it
current. Role-specific profiles (`repo-profile`) build on it.

Output (repo-level, shared by all roles; keep `hiring/` git-ignored):
- `hiring/_repo/inventory.json` — the deterministic checklist
- `hiring/_repo/codebase-map.md` — the map

Scripts are in `scripts/` next to this file. Run them with `python3 -I`. Paths in this file are relative to this skill's folder (the folder that holds this `SKILL.md`); skills are installed side by side, so `../<other-skill>/` reaches a sibling skill. Shared scripts named without a path (`check_ready.py`, `decisions.py`, `focus.py`, `trace_usage.py`, `workspace.py`) are in `../hiring-workspace/scripts/`; `check_map.py` and `inventory.py` are in `../map-codebase/scripts/`; any other script is in `../<skill>/scripts/` of the skill that owns it.

## Procedure

### 1. Inventory (deterministic)

`python3 -I scripts/inventory.py <repo>`

It lists languages and sizes, every manifest, package and compose service, containers, CI/CD pipelines, deployment
and IaC files, migrations and schema files, API specs, auth and security code and tooling, data stores, queues,
ORMs, observability and test frameworks, and the git commit. It records env files but never reads them.
Read its output in full: **everything it lists must be explained in the map.**

### 2. Investigate, area by area

Work through the areas below in order. For each, read the files the inventory points to, follow the code to the
files it depends on, and write down what is true, citing paths. Don't stop at the first file: a pipeline file
tells you the steps; the scripts it calls tell you what they actually do.

| Area | Questions to answer |
|---|---|
| **Overview** | What does the system do? Who uses it? Monolith, services, monorepo? Rough size. |
| **Components and services** | Every package, service and compose service: its job, its entry point, how it talks to the others (HTTP, queues, shared DB). Name each one the inventory lists. |
| **Data stores and schema** | Every database, cache, queue and object store. ORM, main entities, how migrations are written and applied, anything unusual (data migrations, multi-tenancy). |
| **APIs and integrations** | Public and internal APIs (REST, GraphQL, gRPC), how they're defined (spec or code-first), generated clients, external services called (email, payments, LLMs). |
| **Authentication and security** | How users and services authenticate (sessions, JWT, OAuth), password storage, authorisation and permissions, secrets and configuration handling, CORS/CSRF, dependency and secret scanning, security headers. |
| **CI/CD pipeline** | Every pipeline: triggers, jobs, gates (tests, lint, types, coverage), how releases and deployments happen, dependency automation. |
| **Deployment and infrastructure** | Where and how it runs: containers, orchestration, IaC, proxies and TLS, environments (staging, production), configuration per environment, scaling, backups. |
| **Observability** | Logging, metrics, tracing, error reporting, health checks, alerting. |
| **Testing** | Test types and where they live, frameworks, how tests get a database or services, coverage gates, end-to-end tests. |
| **Dependencies** | Main libraries per package and why they matter; anything pinned, forked or unusual. |
| **Conventions** | Code style and lint rules, typing strictness, structure, review rules (CODEOWNERS), commit or release conventions. |
| **Hot spots and risks (INTERNAL)** | What a new engineer will find hardest: complex or fragile areas, most-changed files, missing safeguards, security weaknesses, tech debt. **Never published**: postings and interview questions describe the work, not these findings. |
| **Gaps in this map** | What you didn't verify and why (e.g. "infrastructure lives in another repo"). |

For a large repo or monorepo, map every component at least at the "what it is and how it connects" level, and go deep
on the parts the user says they hire for. If the user hasn't said, ask once which areas matter most.

### 3. Write the map

```markdown
# Codebase map — <repo name>
Commit: <git commit or "none"> · Inventory: <fingerprint from inventory.json> · Generated: <date>

## Overview
...
## Components and services
- **backend** (`backend/`): FastAPI service; entry `backend/app/main.py`; talks to `db` over SQL ...
...
## Hot spots and risks (INTERNAL — never publish)
...
## Gaps in this map
...
```

Rules for the content:
- **Cite evidence** with backticked paths that exist (`backend/app/core/security.py`). A section with nothing to report
  says "None found" and where you checked.
- **Describe, don't copy.** No code blocks longer than a line, and **never** copy secrets, keys, tokens, passwords,
  connection strings or values from env files, even example ones.
- **Be specific.** "JWT access tokens signed with HS256, 8-day expiry (`backend/app/core/config.py`)" beats "uses JWT".
- Keep it under ~400 lines; link to files rather than explaining every function.

### 4. Check it

`python3 -I scripts/check_map.py <repo>` must pass. It fails when a section is missing or cites nothing, a cited
path doesn't exist, something the inventory found isn't explained, the risks section isn't marked INTERNAL, a
secret-looking value was copied, or the codebase changed since the map was written. Fix every error.

### 5. Hand off

Summarise the system for the user in 5–8 lines and offer the next step: planning a hire (`hiring-plan`), writing a
job description, or building a role profile.

## Several repos (workspace)

In a multi-repo workspace (see the `hiring-workspace` skill) each repo is mapped at its tier, written into the
workspace, never into the repo:

| Tier | File | Sections | Check |
|---|---|---|---|
| primary | `<ws>/maps/<repo>/codebase-map.md` | all 13 | `check_map.py <repo path> --map <file>` |
| supporting | `<ws>/maps/<repo>/service-card.md` | overview, components, data, APIs, auth, deployment, dependencies, gaps | `check_map.py <repo path> --map <file> --level card` |

`workspace.py scan` has already written `<ws>/maps/<repo>/inventory.json`. Repos from one template (the scan lists
them): map the group's primary repo fully, and in the others say "same template as <repo>" and describe only what
differs. Mention what each repo publishes and which internal hosts it calls (the inventory's `links`): the system map
builds on that.

**Planning checkpoint (stage `map`)**, per [CHECKPOINTS.md](../hiring-workspace/CHECKPOINTS.md): before mapping, ask
which areas to map in depth (options from the focus and the inventory) and whether template groups share one full
map, nothing pre-selected, with write-your-own and skip options. *If skipped:* every area to the same depth, each
repo mapped on its own. Record with `decisions.py add <ws or hiring/_repo> --stage map …` (`--skipped` for a skip).

## Keeping it current

`check_map.py` compares a fingerprint of the structurally important files (manifests, pipelines, containers,
deployment, migrations, schema, API specs, auth and security code). When they change, the map is stale and every
skill that depends on it stops until you update the affected sections and re-run the inventory.
