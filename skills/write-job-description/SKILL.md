---
name: write-job-description
description: Write a job description for a software engineering role from the company's codebase and a short question-and-answer session with the hiring manager. Describes the real stack and real work without leaking internal details, checks inclusive language, and keeps must-haves consistent with the screening rubric. Use when the user asks to write, draft, improve or review a job description or job posting.
---

# Write Job Description

Produce `hiring/<role-slug>/jd.md`: a public job posting that is specific because it is grounded in
the repo, safe because it reveals nothing internal, and fair because it asks only for what the job needs.

## Principles

- **One question per message, answered before the next.** Prefer multiple choice (use the question tool
  if available) with a free-text option. Never send a list of questions.
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
5. **Pay range.** Recommend including one: it is required in some jurisdictions (for example under pay
   transparency laws in several US states and the EU) and increases applications everywhere. Accept "leave
   it out", and record that choice.
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
4–6 bullets of real work, translated from the repo. Concrete verbs; no internal names.

## Our stack
One line or short list of public technology names, marked "you'll learn the rest" where true.

## Must-haves
3–5 bullets. Capabilities, not years or keywords. Each must trace to the mission or the repo.

## Nice-to-haves
2–4 bullets, explicitly optional.

## Backgrounds we welcome
Transferable experience that counts (e.g. "Django or Rails ORMs count as much as SQLAlchemy").

## How we hire
The steps, how long they take, that applications are reviewed by people with AI-assisted screening,
and how to ask for adjustments or human review.

## What we offer
Benefits from the user, or a clearly marked placeholder.

<Equal opportunity statement from the user, or a placeholder>
```

Writing rules:
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

Tell the user where `jd.md` is and that it is ready to post. Offer, in one line, the next step:
building the screening rubric from it (`hiring-rubric`), or adjusting the existing rubric if the JD changed a must-have.

## Rules

- The user owns the posting. Present facts and recommendations (pay range, shorter must-have list), then follow
  their decision.
- Do not invent benefits, salaries, perks or company facts. Use placeholders like `[benefits]` and list them
  for the user at the end.
- Do not include protected characteristics or proxies for them (age, "young team", "digital native", gender,
  nationality, "native speaker" unless the job truly requires a language level, which you then state as a level).
- If the user pastes an existing JD containing internal details, point them out before rewriting.
