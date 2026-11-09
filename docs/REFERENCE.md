# Reference

[← Back to the README](../README.md)

## Skills

| Skill | What it does | Output |
|---|---|---|
| `hiring-workspace` | For several repos: a private workspace, cross-repo graph, system map; also the focus, decisions log and readiness gate every skill uses | `system/system-map.md`, `roles/<role>/` |
| `map-codebase` | Inventories the repo and writes a whole-system map with file citations: services, data, APIs, auth and security, CI/CD, deployment, observability, tests, risks; gates every other skill | `hiring/_repo/codebase-map.md` |
| `hiring-plan` | Asks follow-up questions one at a time, investigates the relevant part of the repo, proposes 2–3 role designs, writes an approved brief | `brief.md` |
| `repo-profile` | Builds on the map and goes deep on the role's area: stack, architecture, conventions, gaps, hard problems | `repo-profile.md` |
| `write-job-description` | Writes a public job posting from the repo and a short Q&A with you; checks it for leaked internals and biased wording, and keeps its must-haves in line with the rubric | `jd.md` |
| `hiring-rubric` | Turns brief + JD + profile into weighted criteria with observable anchors; waits for approval | `rubric.json` |
| `screen-candidates` | Redacts CVs, scores each one alone with verbatim evidence, validates, ranks and renders the report | `scores/`, `ranking.json`, `report.html`, `report.md` |
| `interview-kit` | Writes core questions shared by all candidates plus personal questions from each CV, validates them and renders printable kits with scorecards | `interviews/` |
| `close-round` | Deletes candidate data when the role closes; keeps a pseudonymous audit record; finds overdue rounds | `audit.json` |

## Scripts (standard-library Python in skills/screen-candidates/scripts/)

| Script | Job |
|---|---|
| `prepare_cvs.py` | Assign ids, extract text (PDF via `pdftotext`, DOCX, MD, TXT), first-pass redaction, injection scan |
| `identities.py` | Confirm or correct each detected candidate name; scoring is blocked until every name is confirmed |
| `check_redaction.py` | Block scoring if a name is unconfirmed, or if names, contact details, age, nationality or links remain |
| `validate_scores.py` | Schema and consistency checks; every evidence quote must appear in the CV; injection CVs must be flagged |
| `rank.py` | Weighted totals, must-have gates, ties; refuses invalid scores |
| `render_report.py` | Builds `report.html` (charts, heatmap, cards; self-contained) and `report.md` from the data |

In `skills/hiring-workspace/scripts/`:

| Script | Job |
|---|---|
| `workspace.py` | Create a workspace, add repos by path or git URL, set tiers, scan, sync, show status, start a role |
| `system_graph.py` | Find links between repos (packages, images, service calls, shared contracts) and template groups |
| `check_system.py` | Block work until every repo is mapped at its tier and the system map explains every link |
| `trace_usage.py` | Where a library is defined, declared, imported and called, per repo (Python, TS/JS, Go, Java/Kotlin) |
| `focus.py` | Check the focus (no criteria about people, no switching off safeguards), version it, find stale outputs |
| `decisions.py` | The decisions log: add, confirm, list pending assumptions |
| `check_ready.py` | The one gate every skill runs: maps, system map, focus and decisions, in either mode |

## Workspace layout

One folder per role, inside the repo you are hiring for. Keep `hiring/` in `.gitignore`.

```text
hiring/_repo/
├── inventory.json      # map-codebase: deterministic inventory
└── codebase-map.md     # whole-system map, shared by every role

hiring/db-owner/
├── brief.md            # hiring-plan, approved by you
├── jd.md               # write-job-description, or your own
├── repo-profile.md     # repo-profile
├── rubric.json         # hiring-rubric, approved by you
├── cvs/                # you provide
├── candidates.json     # id → file
├── identities.json     # id → confirmed name (personal data)
├── extracted/          # raw text: personal data, deleted when the round closes
├── redacted/           # what the model scores
├── prep_report.json    # extraction problems, injection hits, code links (for humans)
├── scores/             # one file per candidate
├── ranking.json
├── report.html         # the report to read and share
├── report.md           # same content as text
├── interviews/         # core.json, one kit per candidate (.json/.html/.md), index.html
├── round.json          # opened/closed dates (retention)
└── audit.json          # written when the round is closed
```

Several repos? Same role folders, in a workspace outside all of them:

```text
~/hiring/payments/
├── workspace.json      # repos and tiers (primary, supporting, ignored)
├── decisions.json      # decisions shared by every role
├── repos/              # clones of repos added by URL
├── maps/<repo>/        # inventory.json + codebase-map.md or service-card.md
├── system/             # system-graph.md (generated), system-map.md
└── roles/payments-engineer/
    ├── focus.md        # what to concentrate on
    ├── decisions.json  # this role's decisions
    └── …               # the same files as hiring/<role>/
```

## Design principles

- **Plan before screening.** The mission and the code decide the criteria, not a keyword list.
- **Rubric first.** No candidate is scored until a named human approves the rubric.
- **Evidence or zero.** Every level quotes the CV; the validator checks the quote exists.
- **Silent ≠ lacking.** "No evidence" is a gap to probe; only an explicit contradiction fails a must-have.
- **Independent scoring** against redacted text; candidates are never compared while scoring.
- **CVs are untrusted.** Injection attempts are detected, flagged and ignored.
- **Names are confirmed, not guessed.** Redaction is only as good as knowing whose CV it is.
- **Ask what matters, once.** At most three questions per stage, nothing pre-selected, always a write-your-own
  and a skip option; a skip is recorded as none, never filled with a guess.

