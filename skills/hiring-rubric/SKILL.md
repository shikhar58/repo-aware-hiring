---
name: hiring-rubric
description: Turn a job description plus the repo profile into a weighted, evidence-based screening rubric for a software engineering role, and get the hiring manager to approve it before any candidate is scored. Use after repo-profile and before screen-candidates.
---

# Hiring Rubric

Produce `hiring/<role-slug>/rubric.json` (machine-readable) and `rubric.md` (human-readable).
The rubric is the contract every candidate is scored against. **No candidate is scored until
a human has approved it.**

## Inputs

- `hiring/<role-slug>/repo-profile.md` — run the `repo-profile` skill first if missing.
- `hiring/<role-slug>/brief.md` if it exists (from `hiring-plan`).
- The job description (a file in `hiring/<role-slug>/` such as `jd.md`, or pasted text).
  If there is a brief but no JD, offer to draft `jd.md` from the brief and let the user edit it.

## Procedure

0. **Start from the brief.** A brief marked `draft` must be confirmed by the user first. When a brief exists, its derived requirements, success criteria
   and anti-goals take priority. Every criterion must trace to the brief's mission, the repo,
   or a hard JD requirement. Anti-goals become exclusions.
1. **Reconcile JD with repo.** List where they agree, where the JD asks for something the repo
   doesn't use, and where the repo demands something the JD omits. Show these gaps to the user;
   they are often the most useful output of the whole tool.
2. **Draft 6–10 criteria.** Each criterion is a capability, not a keyword
   ("designs and debugs async Python services under load", not "asyncio").
3. **Classify and weight.**
   - `must_have`: failing it means not suitable. Keep to 2–4. Each must be justified by the repo
     or by a hard JD requirement.
   - `important` and `nice_to_have`: weighted. Weights across all non-must-have criteria sum to 100.
4. **Write anchors.** For each criterion, describe what CV evidence looks like at levels
   0 (no evidence), 1 (weak/adjacent), 2 (solid), 3 (strong). Anchors must be observable in a CV
   ("designed online migrations on large tables"), not judgments ("good at databases"),
   so two scorers would pick the same level. Include transferable evidence,
   e.g. strong Go concurrency counts toward an async-Python criterion at level 1–2.
5. **List exclusions explicitly** (see Rules). They go into the rubric file so the screener
   sees them every time.
6. **Ask for approval.** Present `rubric.md` and ask the user to approve or edit weights,
   must-haves and anchors. Write `"approved": true` and the approver's name only after they confirm.

## rubric.json schema

```json
{
  "role": "Senior Backend Engineer",
  "role_slug": "senior-backend",
  "version": 1,
  "approved": false,
  "approved_by": null,
  "criteria": [
    {
      "id": "async-services",
      "name": "Designs and debugs async Python services",
      "tier": "must_have | important | nice_to_have",
      "weight": 0,
      "source": "brief | repo | jd (one or more, e.g. \"brief+repo\")",
      "justification": "required for must_have: one line the approver sees",
      "repo_evidence": ["src/api/server.py"],
      "anchors": {"0": "...", "1": "...", "2": "...", "3": "..."},
      "transferable_from": ["Go concurrency", "Node event loop"]
    }
  ],
  "exclusions": [
    "name, photo, age, date of birth, gender, nationality, marital status, religion, disability",
    "employment gaps without further context",
    "prestige of university or employer as a standalone signal"
  ]
}
```

Must-have criteria carry `weight: 0`; they act as gates, not points.

## Rules

- Never create criteria based on protected characteristics or proxies for them
  (age via graduation year, "culture fit", native-speaker requirements unless the JD truly needs a language level).
- Years-of-experience thresholds are allowed only as anchors, never as must-haves.
- Every must-have needs a one-line justification visible to the approver.
- If the user changes the rubric later, bump `version`; previous screening results stay tied to the old version.
