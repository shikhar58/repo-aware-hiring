---
name: write-job-description
description: Write a job description for a software engineering role from the company's codebase and a short question-and-answer session with the hiring manager. Describes the real work and hints at the stack through the work and requirements (no stack list) without leaking internal details, checks inclusive language, and keeps must-haves consistent with the screening rubric. Use when the user asks to write, draft, improve or review a job description or job posting.
---

# Write Job Description

Produce `hiring/<role-slug>/jd.md`: a public job posting that is specific because it is grounded in
the repo, safe because it reveals nothing internal, and fair because it asks only for what the job needs.

## Before anything else: readiness, focus and decisions

Run `python3 -I ${CLAUDE_PLUGIN_ROOT}/skills/hiring-workspace/scripts/check_ready.py <repo-or-workspace> --role <role-slug> --stage jd`
(or the same script relative to this skill: `../hiring-workspace/scripts/check_ready.py`). It works on one repo and on a
multi-repo workspace.
- **NOT READY**: fix what it names and re-run. A missing or stale map → the `map-codebase` skill (or update the sections
  it lists); a missing or stale system map → the `hiring-workspace` skill; a rejected focus → edit `focus.md`. Do not
  continue on a missing or stale map: everything below depends on understanding the whole system, not a sample of it.
- **Read every file it lists** under "Read before starting": the codebase map (one repo), or the system map plus every
  repo's map or service card (workspace), and the focus.
- **Role folder**: the one it prints (`hiring/<role-slug>/` in one repo, `roles/<role-slug>/` in a workspace). Below,
  `hiring/<role-slug>/` means that folder.
- **Focus**: apply it as described in [CHECKPOINTS.md](../hiring-workspace/CHECKPOINTS.md#the-focus), and write the
  version it prints into what you produce. The posting is public, so put it in an HTML comment under the
  title: `<!-- Focus: <version> -->`.

## Planning checkpoint (stage `jd`)

Follow [CHECKPOINTS.md](../hiring-workspace/CHECKPOINTS.md): reuse what `check_ready.py` says is already decided or
skipped, ask this stage's questions one at a time with nothing pre-selected and a write-your-own and a skip option
([How to ask a question](../hiring-workspace/CHECKPOINTS.md#how-to-ask-a-question)), and record each answer with
`decisions.py` (`--skipped` for a skip, stored as none; nothing is guessed in its place). This stage asks:

1. **How much of the system to describe publicly**: options such as "the work only" or "the work plus the
   product's purpose". Technologies are only ever hinted at inside the work, must-haves and nice-to-haves (no stack
   section). In a workspace, `check_jd.py` also blocks distinctive repo, service and package names
   (`checkout-svc`, `acme-payments`); say "our checkout service" instead. *If skipped:* describe the work; never name
   internals.
2. **Pay range** and 3. **location and working pattern**, if the brief doesn't have them (asked in step 1 below).
   *If skipped:* `[insert: …]` placeholders in the draft.
The focus shapes "What you'll work on"; it never adds requirements about the person.

## Principles

- **One question per message, answered before the next.** Prefer multiple choice (use the question tool
  if available), with nothing pre-selected or labelled "recommended", followed by a write-your-own option and a skip
  option ([How to ask a question](../hiring-workspace/CHECKPOINTS.md#how-to-ask-a-question)). A skipped fact becomes an
  `[insert: …]` placeholder. Never send a list of questions.
- **Look before you ask.** Read the brief and the repo first; ask only about intent, priorities, and facts
  the code cannot show (location, salary range, team, benefits).
- **The JD is public.** Anything from the repo must be translated into general language before it goes in.
- **Every must-have must be justified** by the mission or the repo. Short must-have lists attract more
  qualified applicants; long ones put people off, disproportionately those from under-represented groups.

## Inputs

In this order of preference:
1. `hiring/<role-slug>/brief.md` (from `hiring-plan`). If it exists and is approved, most questions are
   already answered: use its mission, scope, success criteria, requirements and anti-goals.
2. `hiring/<role-slug>/repo-profile.md` (from `repo-profile`) for the stack and the real problems.
3. The repo itself, if neither exists. For a role with a specific mission and no brief, suggest running
   `hiring-plan` first, which also produces the material for the JD; continue without it if the user prefers.
4. An existing JD the user pastes or attaches, to improve rather than rewrite from scratch.
5. `hiring/<role-slug>/rubric.json` if it already exists, so the JD matches what will be screened.

## Procedure

### 1. Questions and answers

Ask only what you still need after reading the inputs, one at a time. Typical order:

1. **Role title and level**, with options derived from the brief or repo (e.g. "Backend Engineer",
   "Senior Backend Engineer", "Staff Engineer, Data Platform").
2. **What success looks like in the first 6–12 months**, if there is no brief. Offer options from the repo.
3. **Location and working model**: remote (which time zones), hybrid (where, how many days), on-site.
4. **Employment type**: permanent, fixed-term, contract.
5. **Pay range.** Say, as a fact, that a range is required in some jurisdictions (for example under pay
   transparency laws in several US states and the EU) and tends to increase applications. Options: give a range,
   leave it out, write their own answer, or skip. *If skipped:* `[insert: salary range]` in the draft.
6. **Team and company context**: team size, who they report to, what the company does, in the user's words.
7. **Benefits and anything the company always includes** (equal opportunity statement, visa sponsorship,
   accessibility of the hiring process). Offer to leave a placeholder.
8. **Tone**: plain and direct (default), warm, or formal.

Skip any question the brief already answers, and say which answer you took from it.

### 2. Translate the repo into public language

From the profile and the code, collect: the main languages and frameworks, the kind of system, and the real
problems the hire will work on. Then rewrite each for the public:

| From the repo (never publish) | In the JD |
|---|---|
| "Migrations run in `backend/scripts/prestart.sh` on every container start" | "Make our schema changes safe to ship without downtime" |
| "No backups or replication configured" | "Own the reliability of our PostgreSQL databases: backups, pooling, monitoring" |
| "Offset pagination on the items endpoint is slow" | "Find and fix performance problems as our data grows" |
| Internal service, repo, host or customer names | Generic descriptions ("our payments service") or nothing |

Never publish: file paths, internal names, hostnames, environment variable names, version numbers of
internal tools, security weaknesses, incidents, customer names, or anything that reads like a vulnerability.
Public technology names (PostgreSQL, Python, FastAPI) are fine.

### 3. Draft section by section

Present each section (~100–200 words) and get a yes or edits before the next. Sections, in this order:

```markdown
# <Role title>
<Location / working model> · <Employment type> · <Pay range or "Pay range: on request">

## About the role
2–4 sentences: the mission and why it matters now.

## What you'll work on
4–6 bullets of real work, translated from the repo. Concrete verbs; no internal names. Technologies can show
through the work itself ("tune hybrid keyword and vector search", "make Postgres schema changes safe").

## Must-haves
3–5 bullets. Capabilities, not years or keywords. Each must trace to the mission or the repo.
Where a technology matters, name it as an example of the capability, among alternatives.

## Nice-to-haves
2–4 bullets, explicitly optional. The natural place for the rest of the stack, again as examples.

## How we hire
The steps and timeline only if the user gave them; otherwise placeholders, never generic text:
[insert: interview steps and how long they take]
[insert: how AI-assisted screening is used and how to ask for adjustments or a human-only review; required in some jurisdictions]

## What we offer
[insert: benefits], unless the user gave them.

[insert: equal opportunity statement], unless the user gave one.
```

The output is a **draft for the hiring manager to finish**, not a final posting. Start the file with
`<!-- DRAFT: fill every [insert: …] placeholder and review before publishing -->` under the title. Write only what
the code, the brief or the user's answers support; everything else (pay, location details, hiring steps, timeline,
benefits, team facts, equal opportunity statement) is an `[insert: …]` placeholder. Optional sections the manager may
add themselves, such as transferable backgrounds or team context, are left out of the draft unless the user asks.

Writing rules:
- **No stack section.** Companies rarely want to publish their exact stack, and a list invites keyword-matching
  applicants. Let the technologies show through the work and the requirements instead: in **What you'll work on**
  as part of the task ("tune keyword and vector search"), and in **Must-haves** and **Nice-to-haves** as examples of a
  capability, mixed with credible alternatives: "production Python libraries", "vector databases such as Qdrant, pgvector or
  Elasticsearch", "language-processing tools such as spaCy or NLTK". A reader who knows the field can tell what you
  work with; nobody gets an inventory. Mention only technologies the role really touches, never internal tools or
  versions. Add an explicit "Our stack" section only if the hiring manager asks for one (record it as a decision;
  `check_jd.py` warns about a stack section otherwise).
- Second person ("you'll"), short sentences, no buzzwords ("rockstar", "ninja", "fast-paced", "wear many hats").
- Requirements describe capabilities ("has shipped schema migrations on production data"), not years
  ("5+ years of PostgreSQL") or proxies (degrees, specific employers).
- If the screening rubric exists, each rubric must-have appears in **Must-haves** (same meaning, public wording),
  and nothing is a JD must-have that the rubric does not treat as one. If the rubric does not exist yet, tell the
  user the JD's must-haves will seed it.

### 4. Check it

Run `python3 -I scripts/check_jd.py hiring/<role-slug>` (the script lives next to this file;
`${CLAUDE_PLUGIN_ROOT}/skills/write-job-description/scripts/check_jd.py` when installed).
- **Errors** (exit code 1) are possible leaks of internal details: fix every one, then re-run.
- **Warnings** are inclusive-language, structure and consistency issues. Fix them or tell the user why one is
  intentional. Show the user what you changed.

### 5. Hand off

Tell the user where `jd.md` is, that it is a draft, and list the placeholders they need to fill before posting. Offer, in one line, the next step:
building the screening rubric from it (`hiring-rubric`), or adjusting the existing rubric if the JD changed a must-have.

## Rules

- The user owns the posting. Present facts (why a pay range helps, why a short must-have list works), then follow
  their decision.
- Do not invent benefits, salaries, perks, hiring steps or company facts. Use placeholders like `[insert: benefits]` and list them
  for the user at the end.
- Do not include protected characteristics or proxies for them (age, "young team", "digital native", gender,
  nationality, "native speaker" unless the job truly requires a language level, which you then state as a level).
- If the user pastes an existing JD containing internal details, point them out before rewriting.
