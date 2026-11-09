---
name: repo-profile
description: Build or refresh a role-specific engineering profile on top of the codebase map (stack, architecture, conventions, test culture, hard problems for the role's area) to ground software engineer hiring. Use after map-codebase and before creating a hiring rubric, or when the user asks what skills a part of their codebase demands.
---

# Repo Profile

Produce `hiring/<role-slug>/repo-profile.md`, built on top of the whole-system map from `map-codebase`: a compact,
evidence-backed description of what
working in this codebase actually requires. It is built **once per role** and reused for every
candidate, so the repo is never re-read per CV.

## Before anything else: readiness, focus and decisions

Run `python3 -I ../hiring-workspace/scripts/check_ready.py <repo-or-workspace> --role <role-slug> --stage profile`. It works on one repo and on a
multi-repo workspace. Paths in this file are relative to this skill's folder (the folder that holds this `SKILL.md`); skills are installed side by side, so `../<other-skill>/` reaches a sibling skill. Shared scripts named without a path (`check_ready.py`, `decisions.py`, `focus.py`, `trace_usage.py`, `workspace.py`) are in `../hiring-workspace/scripts/`; `check_map.py` and `inventory.py` are in `../map-codebase/scripts/`; any other script is in `../<skill>/scripts/` of the skill that owns it.
- **NOT READY**: fix what it names and re-run. A missing or stale map → the `map-codebase` skill (or update the sections
  it lists); a missing or stale system map → the `hiring-workspace` skill; a rejected focus → edit `focus.md`. Do not
  continue on a missing or stale map: everything below depends on understanding the whole system, not a sample of it.
- **Read every file it lists** under "Read before starting": the codebase map (one repo), or the system map plus every
  repo's map or service card (workspace), and the focus.
- **Role folder**: the one it prints (`hiring/<role-slug>/` in one repo, `roles/<role-slug>/` in a workspace). Below,
  `hiring/<role-slug>/` means that folder.
- **Focus**: apply it as described in [CHECKPOINTS.md](../hiring-workspace/CHECKPOINTS.md#the-focus), and write the
  version it prints into what you produce (`Focus: <version>` in Markdown headers, `"focus_version"` in JSON).

## Planning checkpoint (stage `profile`)

Follow [CHECKPOINTS.md](../hiring-workspace/CHECKPOINTS.md): reuse what `check_ready.py` says is already decided or
skipped, ask this stage's questions one at a time with nothing pre-selected and a write-your-own and a skip option
([How to ask a question](../hiring-workspace/CHECKPOINTS.md#how-to-ask-a-question)), and record each answer with
`decisions.py` (`--skipped` for a skip, stored as none; nothing is guessed in its place). This stage asks:

1. **Order of the hard problems**: offer orderings drawn from the focus and from the risks in the maps.
   *If skipped:* order by the risk the maps show, and say so in the profile.
2. **Coverage** (workspace): which repos and modules to cover in depth. *If skipped:* primary repos in depth,
   supporting repos where the system map's connections touch them. Cross-repo problems (a contract between two
   services, a library used by both) count as hard problems. Cite paths with the repo name:
   `checkout-svc:app/api/orders.py`.
If the focus names a library and `usage-<library>.md` doesn't exist yet, run `trace_usage.py` first and cite it.

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

1. **Start from the codebase map.** The whole-system picture (components, data, APIs, auth and security,
   CI/CD, deployment, observability, testing) is already in the codebase map (and, in a workspace, the system map and each repo's map or card). Don't redo it:
   select what matters for this role and cite the map's findings with their paths.
2. **Go deep on the role's scope.** For each module in scope, read the entry points, the core domain files,
   the tests, how it is built and deployed (from the map's CI/CD and deployment sections), and the most-changed
   source files.
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
