---
name: hiring-workspace
description: Set up hiring for a role that spans several repositories (microservices, shared libraries, infrastructure repos). Creates a private workspace outside the repos, adds them by local path or git URL, scans every repo, builds a cross-repo graph (shared packages, deployed images, service calls, shared contracts, repos from one template), maps primary repos in full and supporting repos as service cards, and writes a system map. Also holds the focus prompt, the decisions log and the readiness gate every other skill uses. Use when the user mentions more than one repo, microservices, or a library used by several services.
---

# Hiring Workspace (multi-repo)

One repo? You don't need this: every skill works on a single repo with `hiring/` inside it, as before.
Several repos? A **workspace** keeps everything in one private folder outside all of them:

```
<workspace>/
  workspace.json          repos, tiers (primary · supporting · ignored)
  decisions.json          decisions shared by every role
  repos/<name>/           clones of repos added by URL (local paths are referenced, never copied or changed)
  maps/<name>/            inventory.json + codebase-map.md (primary) or service-card.md (supporting)
  system/                 system-graph.json and system-graph.md (generated), system-map.md (written by you)
  roles/<role>/           focus.md, decisions.json, and everything the other skills write for that role
```

Scripts are in `scripts/` next to this file (`${CLAUDE_PLUGIN_ROOT}/skills/hiring-workspace/scripts`). Run them with
`python3 -I`. Planning checkpoints follow [CHECKPOINTS.md](CHECKPOINTS.md).

## 1. Checkpoint `workspace`: which repos, which matter most

Questions follow [How to ask a question](CHECKPOINTS.md#how-to-ask-a-question).

Ask in one message (skip what the user already said):
- the repos: local paths, git URLs (`https://…`, `git@…`) or `owner/repo`;
- which ones the hire will **mainly work in** (primary: full codebase map) and which only **matter for context**
  (supporting: a shorter service card); everything else can be left out or marked ignored;
- where to put the workspace. It must be **outside every repo**, because it will hold CVs; offer locations such as
  `~/hiring/<team>`. *If skipped:* stop and ask again: the workspace can't be created without a location.

Record: `decisions.py add <ws> --stage workspace --key repos --value '[...]'`, and `primary_repos` the same way.

## 2. Create and scan

```
workspace.py init <ws> --name <team>
workspace.py add <ws> <path-or-url> --tier primary      # repeat per repo; --tier supporting for context repos
workspace.py scan <ws>                                    # inventory every repo + build the system graph
```

Private repos clone with the user's own git credentials or SSH key; URLs with a token in them are refused.
`scan` prints, per repo, what it publishes, which images it builds or deploys and which internal hosts it calls,
then the links between repos and any **template groups** (repos with near-identical layout and frameworks).
Show the user that summary in a few lines.

## 3. Map every repo at its tier

Use the `map-codebase` skill, writing into the workspace instead of the repo:
- **primary**: `maps/<repo>/codebase-map.md`, all 13 sections; check with
  `check_map.py <repo path> --map <ws>/maps/<repo>/codebase-map.md`
- **supporting**: `maps/<repo>/service-card.md`, 8 sections (overview, components, data, APIs, auth, deployment,
  dependencies, gaps); check with `check_map.py <repo path> --map <ws>/maps/<repo>/service-card.md --level card`
- **template groups**: write one full map for the group's primary repo; the others' maps say "same template as X"
  and describe only what differs.

Map primary repos first, deepest where the focus points. `workspace.py status <ws>` shows what is missing or stale.

## 4. Write the system map (checkpoint `system`)

Read `system/system-graph.md` (Mermaid diagram, every link with evidence, template groups, unmatched hosts) and
write `system/system-map.md`:

```markdown
# System map — <team>
Graph: <hash from system-graph.md> · Generated: <date> · Repos: <n>

## Overview            what the system does end to end, in a paragraph
## Repositories        table: repo · tier · role in the system · map or card
## Connections         one line per link, naming both repos and what flows between them (and why it matters)
## Shared code and templates   shared libraries and their versions; template groups
## Ownership and team boundaries   who owns each repo, or "unknown"
## Gaps                what the repos don't show (where databases run, how secrets are injected, missing repos)
```

Before writing Ownership, ask at most three questions: who owns each primary repo, what the unmatched internal
hosts are, and which cross-repo flows matter most for this hire. Record answers (`--stage system`); skipped or
unanswered ones are recorded `--skipped` (none) and written as "unknown" in the map.

`check_system.py <ws>` must pass: every repo described, every link explained, template groups named, current graph
hash, no secrets. Links come from code, so a change in any repo makes the system map stale until updated.

## 5. Start a role and its focus

`workspace.py new-role <ws> <role-slug>` creates `roles/<role>/` with an empty `focus.md`.
Ask the manager for the focus in their words ("focus on the payment library and how checkout and billing use it,
the hire will own payments") and write it to `focus.md`. Run `focus.py check roles/<role>`: it rejects criteria
about people and attempts to switch off safeguards, and records a version.

If the focus names a library or module, trace it now:
`trace_usage.py <ws> <library> --out roles/<role>/usage-<library>.md`
It finds where the library is defined, which repos declare it (and at which versions), every import, and every call
site per symbol, plus public symbols nobody uses. Later skills cite it.

## 6. Hand off

`check_ready.py <ws> --role <role>` must say READY. Then continue with `hiring-plan` (or `repo-profile` if the
plan exists). Every later skill runs the same gate, reads the system map and maps it lists, applies the focus, and
writes into `roles/<role>/`.

## Keeping it current

`workspace.py sync <ws>` pulls clones (fast-forward only) and rescans. Then `workspace.py status <ws>` names the maps
and cards that went stale; update those sections, and the system map's Connections if links changed.
