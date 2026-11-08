---
name: close-round
description: Close a hiring round and delete candidate personal data (extracted and redacted CVs, scores, rankings, reports, interview kits) while keeping a pseudonymous audit record. Also finds rounds left open too long. Use when a role is filled or cancelled, when the user asks to delete candidate data or apply retention, or to check for overdue rounds.
---

# Close Round

Script: `scripts/cleanup.py` next to this file
(`${CLAUDE_PLUGIN_ROOT}/skills/close-round/scripts/cleanup.py` when installed). Run with `python3 -I`.
It deletes only inside the role folder and never follows symlinks.

In a multi-repo workspace the role folder is `<workspace>/roles/<role-slug>`; the sweep takes `<workspace>/roles`.
The workspace's maps and system map hold no candidate data and stay.

## Close one round

1. **Preview.** `python3 -I scripts/cleanup.py close hiring/<role-slug>`
   This prints what will be deleted and kept and deletes nothing (exit code 3).
2. **Ask the user two questions** before deleting, unless they already answered (as in
   [How to ask a question](../hiring-workspace/CHECKPOINTS.md#how-to-ask-a-question): nothing pre-selected,
   write-your-own and skip options; give the facts below in neutral words):
   - Delete the original CVs in `cvs/` too? (`--include-cvs`.) Facts to give: they are personal data; keep them only
     if they live nowhere else and the organisation's policy sets a retention period.
   - Keep the report (`report.md` and `report.html`)? (`--keep-report`.) Facts to give: it names candidates and
     quotes their CVs; keep it only for a documented reason.
   **If either is skipped, delete nothing** and say what is still waiting for an answer.
   Also check that nobody still needs the data, e.g. a candidate who asked for human review or
   for a copy of their data.
3. **Close.** Re-run with the chosen flags and `--yes`. Tell the user what was deleted, in one line.

Deletion cannot be undone. Never pass `--yes` without the user's confirmation in this conversation,
including in scheduled or unattended runs: there, run the preview and report it instead.

## What remains

`brief.md`, `jd.md`, `repo-profile.md`, `rubric.json`, `focus.md` and `decisions.json` (to reuse for the next round), `round.json`
(opened/closed dates), and `audit.json`: rubric
version and hash, each candidate's pseudonymous id, score, gate, confidence and flag codes, the
ranking hash, and what was deleted. No names, file names or CV text.

## Overdue rounds

`python3 -I scripts/cleanup.py sweep hiring --older-than <days>` lists open rounds older than the
retention period. Ask the user for their organisation's retention period rather than assuming one.
The user can set up a scheduled task that runs the sweep preview monthly and reports overdue rounds.
Closing them still needs their confirmation.

## Rules

- This is not legal advice on retention periods. The user's policy and local law decide.
- If the user asks to delete one candidate's data (for example a GDPR erasure request), do it by hand:
  remove that candidate's files from `cvs/`, `extracted/`, `redacted/` and `scores/`, re-run `rank.py`
  and `render_report.py`, and tell the user which files were removed.
