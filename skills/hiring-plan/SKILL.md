---
name: hiring-plan
description: Plan a software engineering hire collaboratively before any screening. Asks follow-up questions one at a time, investigates the relevant part of the repo, proposes 2–3 role designs with trade-offs, and writes an approved hiring brief. Use when the user describes a hiring need ("someone to migrate this service to Rust", "an owner for our database layer", "we need help scaling ingestion"), or before repo-profile when no brief exists.
---

# Hiring Plan

Turn a loose hiring need into `hiring/<role-slug>/brief.md`: the mission, the exact part of the
repo, what success looks like, and the role shape the user chose. Every later skill reads the brief.

**Do not jump to a job description or rubric.** The value of this step is the conversation.

## Before anything else: a current map of the codebase

Run `python3 -I ${CLAUDE_PLUGIN_ROOT}/skills/map-codebase/scripts/check_map.py <repo>` (or the same script relative
to this skill: `../map-codebase/scripts/check_map.py`). If it fails because the map is missing, incomplete or stale,
run the `map-codebase` skill first (or update the sections it names) and re-run until it passes. Do not continue on a
missing or stale map: everything below depends on understanding the whole system, not a sample of it.
Read `hiring/_repo/codebase-map.md` before going on.

## Principles

- **One question per message.** Never send a list of questions. Wait for the answer.
- **Prefer multiple choice.** Offer 2–4 concrete options (use the question tool if available),
  always allowing a free-text answer. Open questions only when options would be guesses.
- **Look before you ask.** If the repo can answer a question, read it instead of asking.
  Ask the user about intent, priorities and constraints, not facts the code shows.
- **Show your evidence.** When you state something about the repo, name the path.
- **YAGNI for roles.** Push back gently on wish-list roles ("Rust + Kubernetes + ML + React").
  Every requirement should trace to the mission.
- **Question the premise once.** If the evidence suggests hiring is not the best answer
  (a 3-week task, a skill the team nearly has), say so and offer alternatives
  (contractor, upskilling, pairing). Then respect the user's decision.

If the user is not available to answer (a scheduled or unattended run), take the most
reasonable answer to each question from the repo and what the user already said, and record
every assumption under **Planning conversation** in the brief with `Status: draft — assumptions not
confirmed`. A draft brief cannot feed an approved rubric until the user confirms it.

## Phase 1 — Understand the mission

Start from what the user said. Identify the **mission type**, confirming with them:

| Mission type | Example | What to investigate in the repo |
|---|---|---|
| Migration | "Rust migration of the parser" | Current language and size of the target code (LOC), hot paths, FFI or service boundaries, test coverage of the module, build tooling, existing Rust if any |
| Area ownership | "Own the database layer" | Schema and migrations folders, ORM vs raw SQL, query patterns, indexes, migration tool, backup or replication config, slow-query hints |
| Scaling / performance | "Ingestion can't keep up" | Concurrency model, queues, batching, caching, profiling or benchmark files, infra config |
| Stabilisation | "Too many incidents in payments" | Error handling, retries, tests, observability, recent churn (`git log` on the area) |
| Greenfield | "New mobile app" | What exists to integrate with (APIs, auth, shared libraries), conventions to keep |
| Capacity | "Just more hands on the backend" | Most-changed areas, open TODOs, where reviews queue up |

Then ask, one at a time, only what you still need. Typical sequence:

1. **Scope:** "Which part of the repo is this?" Propose paths you found; let them confirm or narrow.
2. **Outcome:** "What should be true in 6 months if this hire works out?" Offer options derived
   from the mission (e.g. "parser fully in Rust behind the same API" / "Rust core with Python
   bindings" / "a migration plan plus first module shipped").
3. **Autonomy and seniority:** "Will they lead this alone or join someone?"
4. **Constraints:** timeline, budget band, location or time zone, permanent vs contract.
   Ask only those that change the role design.
5. **Team context:** "What does the current team already cover well?" Use the repo to propose
   an answer and ask them to correct it.

Stop asking when you can propose designs. Usually 4–7 questions.

## Phase 2 — Investigate the scoped area

Start from the codebase map's sections for the scoped area, then read the scoped paths with the mission lens from the table above. Summarise in 5–10 bullets
with paths: size, complexity, risks, what a newcomer would struggle with first.
Share this summary with the user and ask whether it matches their understanding.
Their corrections are often the most important input.

## Phase 3 — Propose role designs

Offer **2–3 distinct role shapes** with trade-offs and your recommendation. Example for a Rust migration:

- **A. Senior Rust engineer, migration lead.** Owns design and delivery. Fastest, hardest to find, highest cost.
- **B. Strong systems engineer (C++/Go) who has shipped some Rust.** Wider talent pool; needs
  2–3 months to ramp on Rust idioms; pair with code review support.
- **C. Contractor for the migration, plus upskilling one internal engineer.** Best if the
  work is bounded and the team must own Rust afterwards.

For each: who it suits, what it optimises for, main risk, and what must be true about the
team for it to work. Lead with the one you recommend and say why, tied to the evidence.

## Phase 4 — Write the brief in sections

Present the brief in short sections (~150–250 words each) and confirm each before moving on:
mission → scope → success criteria → role shape → derived requirements → anti-goals.
Then write `hiring/<role-slug>/brief.md`:

```markdown
# Hiring brief — <role title>
Date: <date> · Owner: <user> · Status: approved

## Planning conversation (summary)
<one line per question asked and the answer chosen>

## Mission
<1–3 sentences>

## Scope in the repo
- <paths> — <why they matter>

## What we found
<the Phase 2 bullets, with paths>

## Success looks like
- 3 months: …
- 6 months: …
- 12 months: …

## Chosen role shape
<A/B/C and why; options considered and rejected, one line each>

## Requirements derived from the mission
| Requirement | Why (mission or repo evidence) | Must-have? |
|---|---|---|

## Transferable backgrounds we welcome
<e.g. C++ or Go systems work for a Rust migration>

## Anti-goals
<what this role is NOT; skills we will not screen for>

## Open questions
<anything unresolved>
```

## Hand-off

After the brief is approved:
- `repo-profile` uses **Scope in the repo** as its scope and adds a mission-focused section.
- `write-job-description` turns the brief into a public job posting (`jd.md`), asking only the
  questions the brief doesn't answer (location, pay range, benefits).
- `hiring-rubric` turns **Requirements derived from the mission** into criteria.
- Tell the user the next step in one line and ask whether to continue.
