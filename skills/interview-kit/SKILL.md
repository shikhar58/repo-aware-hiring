---
name: interview-kit
description: Design interview questions for each shortlisted software engineering candidate from the codebase, the job description, the rubric and that candidate's CV. Produces a structured kit (the same core questions for every candidate, plus personal deep-dives into their claims and probes for must-haves their CV didn't show) with what good answers sound like, warning signs and a 0–3 scorecard. Use after screening, when the user asks for interview questions, an interview plan or a scorecard for candidates.
---

# Interview Kit

Produce, for one role:
- `hiring/<role-slug>/interviews/core.json`: core questions asked of **every** candidate, one or more per
  must-have and important criterion.
- `hiring/<role-slug>/interviews/<candidate-id>.json`: personal questions for that candidate.
- Rendered kits `interviews/<candidate-id>.html` (printable scorecard) and `.md`, via `render_kit.py`.

Scripts are in `scripts/` next to this file (`${CLAUDE_PLUGIN_ROOT}/skills/interview-kit/scripts` when installed).
Run them with `python3 -I`.

## Why this structure

Structured interviews, where every candidate answers the same core questions and is rated against the same anchors,
predict job performance better and are fairer than free-form ones, and are easier to defend if a decision is
challenged. Personal questions add depth: they test the claims on this candidate's CV and fill gaps the CV left open.
They never replace the core questions.

## Before anything else: readiness, focus and decisions

Run `python3 -I ${CLAUDE_PLUGIN_ROOT}/skills/hiring-workspace/scripts/check_ready.py <repo-or-workspace> --role <role-slug> --stage interview`
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
  version it prints into what you produce (`Focus: <version>` in Markdown headers, `"focus_version"` in JSON).

## Planning checkpoint (stage `interview`)

Follow [CHECKPOINTS.md](../hiring-workspace/CHECKPOINTS.md): reuse what `check_ready.py` says is already decided or
skipped, ask this stage's questions one at a time with nothing pre-selected and a write-your-own and a skip option
([How to ask a question](../hiring-workspace/CHECKPOINTS.md#how-to-ask-a-question)), and record each answer with
`decisions.py` (`--skipped` for a skip, stored as none; nothing is guessed in its place). This stage asks:

1. **Panel split**: one interviewer, or several, each owning some criteria. Write a panel to `core.json` as
   `"panel"` (see the schema below); `validate_kit.py` checks that every core question has an interviewer and fits
   their slot. *If skipped:* no panel; one interviewer asks everything.
2. **Length and stage** of the interview. *If skipped:* 60 minutes, first technical interview, stated in the kit.
3. **Which candidates**: the shortlist size from screening (`decisions.py get <role> shortlist_size`), or ask.
   *If skipped:* kits for every ranked candidate who meets the must-haves.
Core questions follow the focus: the parts of the system it names come first.

## Inputs

- `rubric.json` (approved), `repo-profile.md`, and `brief.md` / `jd.md` if present.
- `scores/<id>.json` and `redacted/<id>.md` for each candidate. Work from the **redacted** CV only.
- `ranking.json`, to know which candidates to prepare for. Default: the candidates the user names; otherwise ask
  ("the top 5?", "everyone who meets the must-haves?") with options.

## Procedure

1. **Ask two things, one at a time,** unless already known: how long the interview is (30 / 45 / 60 / 90 minutes)
   and which stage it is for (technical deep-dive, hiring-manager conversation, or both). Fit the kit to the time.

2. **Write the core questions once** (`core.json`), before looking at any candidate:
   - One question per must-have and per important criterion; nice-to-haves only if time allows.
   - Ground each in the repo's real problems, but phrase it **for the candidate**, who will hear it: describe a
     scenario in general terms ("Imagine schema migrations run automatically when each app instance starts, and you
     run several instances…"). Never name internal files, services or hosts, and never reveal security weaknesses.
   - Prefer "tell me about a time you…" (past behaviour) and realistic scenarios over trivia or puzzles.
   - For each: 1–2 follow-ups, what a strong answer includes (`listen_for`), warning signs, and minutes.

3. **Write personal questions per candidate** (`<id>.json`), 2–5 of them:
   - `claim_deep_dive`: take a claim from their CV that matters for a criterion, quote it **verbatim** in `evidence`,
     and ask them to go deeper (how, why, what went wrong, what they'd do differently). Test the claim; don't assume it.
   - `gap_probe`: required for every must-have whose status is `no_evidence` or `weak`, recommended for important
     criteria with those statuses. Ask in a way that lets someone with unlisted experience show it.
   - `consistency`: only when claims on the CV conflict; ask neutrally, never accusingly.
   - `why` explains to the interviewer what the question tests; it is not read aloud.
   - Don't repeat a core question. If the core question already covers a gap, add a personal follow-up instead.

4. **Add `notes_for_interviewer`**: 1–3 short points, e.g. which criteria matter most for this person, or that the CV
   was flagged for possible prompt injection (assess the person on their answers; the flag is about the document).

5. **Validate**: `python3 -I scripts/validate_kit.py hiring/<role-slug>`. Fix every error. It checks coverage of
   must-haves, gap probes, that quoted claims are really in the CV, the time budget, and that candidate-facing text
   contains no internal details and no questions about protected characteristics.

6. **Render**: `python3 -I scripts/render_kit.py hiring/<role-slug>`. Tell the user where the kits are and offer to
   adjust any question.

## Schemas

`core.json`:
```json
{
  "rubric_version": 1,
  "duration_minutes": 60,
  "stage": "technical deep-dive",
  "questions": [
    {
      "id": "core-migrations",
      "criterion": "migrations",
      "question": "Tell me about a schema change you shipped on a large production table. How did you avoid downtime?",
      "follow_ups": ["What would you do differently next time?"],
      "listen_for": ["expand-contract or backward-compatible steps", "batched backfills", "a rollback plan"],
      "warning_signs": ["only ever ran migrations generated by a tool, on small data"],
      "minutes": 10
    }
  ],
  "focus_version": "bbebe17d2686",
  "panel": [
    {"interviewer": "Payments lead", "criteria": ["idempotency", "payments-domain"], "minutes": 30},
    {"interviewer": "Platform engineer", "criteria": ["migrations", "deploys"], "minutes": 30}
  ]
}
```

`panel` is optional. Each question (core and personal) goes to the interviewer whose criteria include its criterion;
a question can name `"interviewer"` itself. Kits show who asks what and a panel table. Use role labels, not names.

`<id>.json`:
```json
{
  "candidate_id": "C01",
  "rubric_version": 1,
  "questions": [
    {
      "id": "p1",
      "criterion": "query-perf",
      "type": "claim_deep_dive | gap_probe | consistency",
      "question": "You cut p95 latency on account listing from 900 ms to 40 ms. How did you find the bottleneck?",
      "evidence": ["Cut p95 latency of account listing from 900 ms to 40 ms"],
      "why": "Tests whether the result came from their own diagnosis.",
      "follow_ups": ["What did EXPLAIN show before and after?"],
      "listen_for": ["reads query plans", "measured before and after"],
      "warning_signs": ["can't say what changed in the plan"],
      "minutes": 6
    }
  ],
  "notes_for_interviewer": ["Strong on migrations; spend time on operations."]
}
```

## Rules

- Never ask about, or hint at: age, date of birth, family, marriage, children or pregnancy, religion, nationality or
  where someone is "from", native language or accent, health or disability, ethnicity, gender, sexuality, union
  membership, political views, or employment gaps' reasons. Right-to-work questions belong to HR, worded identically
  for everyone, and are not part of this kit.
- Never use information that was removed by redaction, even if you saw it earlier.
- The kit supports the interviewer's judgement; it does not score candidates. Ratings are given by people, against the
  rubric's anchors, after the interview.
- Interview kits contain candidate data and are deleted when the round is closed (`close-round`).
