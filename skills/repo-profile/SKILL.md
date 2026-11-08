---
name: repo-profile
description: Build or refresh an engineering profile of the company codebase (stack, architecture, conventions, test culture, hard problems) to ground software engineer hiring. Use before creating a hiring rubric, or when the user asks what skills their codebase actually demands.
---

# Repo Profile

Produce `hiring/<role-slug>/repo-profile.md`: a compact, evidence-backed description of what
working in this codebase actually requires. It is built **once per role** and reused for every
candidate, so the repo is never re-read per CV.

## Inputs

- The repository (current working directory unless the user names another path).
- `hiring/<role-slug>/brief.md` if it exists (from `hiring-plan`). Use its **Scope in the repo**
  as the scope and its **Mission** as the lens. If the user describes a specific mission
  (a migration, owning an area, scaling a system) and there is no brief, suggest running
  `hiring-plan` first; continue without it only if they decline.
- Otherwise, the area of the repo the role will own (e.g. `services/billing`, `frontend/`).
  If the user names a role but not an area, ask once which parts of the repo it touches;
  if they don't know, profile the whole repo and say so.

## Procedure

1. **Map the repo cheaply first.** List top-level structure, manifests and config:
   `package.json`, `pyproject.toml`, `requirements*.txt`, `go.mod`, `Cargo.toml`, `pom.xml`,
   `build.gradle`, `Dockerfile`, `docker-compose*`, `*.tf`, CI files (`.github/workflows`,
   `.gitlab-ci.yml`), `Makefile`, lint/format configs. Do not read every source file.
2. **Sample, don't scan.** For each major module in scope, read a handful of representative
   files: an entry point, a core domain file, a test file, and the most-changed source files.
   To find churn, when git history is present (a shallow clone has none; skip this then), limit to the
   last two years, to files that still exist, and drop lockfiles and docs:
   ```bash
   git log --since="2 years ago" --format= --name-only -- <scope> | sort | uniq -c | sort -rn \
     | awk '{print $2}' | while read -r f; do [ -f "$f" ] && echo "$f"; done \
     | grep -Ev '(\.lock|lock\.json|\.md|\.txt)$' | head -10
   ```
3. **Extract signals** — each with a file path as evidence:
   - Languages and versions; frameworks and key libraries (with how central each is).
   - Architecture: monolith/services, sync/async, data stores, queues, infra-as-code, cloud.
   - Conventions: typing strictness, lint rules, error handling style, module layout.
   - Testing culture: test types present, rough test-to-source ratio, CI gates.
   - Hard problems: concurrency, performance-sensitive paths, data migrations, security
     boundaries, complex domain logic, legacy areas.
   - Operational load: observability, on-call hints, deployment complexity.
4. **Separate "core" from "incidental."** A library used in one script is not a hiring
   requirement. Mark each technology as `core`, `regular`, or `incidental`.
5. **Look for what is missing, not only what exists.** In a small or early codebase the hard part
   of the role is often practices the code does not have yet (no backups, migrations run at app
   start, no test isolation). Record gaps with the path that shows the gap. Say explicitly when
   the code is small, so the rubric draws on the mission rather than rewarding familiarity
   with a codebase any good engineer would learn in a week.

## Output format

Write `hiring/<role-slug>/repo-profile.md`:

```markdown
# Repo profile — <repo name> — <role or area>
Generated: <date> · Scope: <paths> · Commit: <short sha or "no git">

## Stack
| Technology | Centrality | Evidence |
|---|---|---|
| Python 3.12 | core | pyproject.toml; src/** |

## Architecture
<3–6 bullets, each with a path>

## Conventions & quality bar
<bullets with paths>

## Hard problems a new hire will meet
<bullets with paths — these become the most valuable rubric criteria>

## Mission lens (only when a brief exists)
<what the mission specifically demands of this code: e.g. for a Rust migration, the modules
to port, their size, boundaries and test coverage; for database ownership, schema size,
migration tooling and risky queries — with paths>

## Transferable vs. specific
- Skills that transfer from other stacks: <e.g. async I/O, relational modelling>
- Skills that are genuinely stack-specific: <e.g. deep LangGraph internals>
```

## Rules

- Never copy secrets, credentials, customer data, or large code blocks into the profile.
  Paths and short identifiers only.
- The profile describes the codebase, not people. Do not include commit authors.
- Prefer "transferable" framing: the rubric built from this must not reward stack keyword
  matching over underlying ability.
- Keep it under ~150 lines so downstream skills can load it cheaply.
