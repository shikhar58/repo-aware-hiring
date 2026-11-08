# Dry run — 2026-11-08

All four skills were run end to end on the public
[full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)
for the mission "someone to own the backend database layer", with 12 synthetic CVs
(see `evals/fixtures/db-owner`). The hiring manager's planning answers were simulated.
Output: `docs/example-report.md`.

## Outcome

- The ranking matched the intended tiers exactly (pairwise accuracy 1.00).
- The candidate who states "no relational database experience" was gated below the line.
- Both injection CVs were detected by the scanner (one hidden as white text in a PDF) and
  flagged; neither gained score.
- Name, gender and national-origin swaps redacted to byte-identical text.

## Problems found and fixed

| # | Problem | Fix |
|---|---|---|
| 1 | Redaction replaced the name before the email, so `ana.ferreira@…` became `[NAME].[NAME]@…` and the checker missed it | Structured PII is redacted first, then the name line, then name tokens |
| 2 | Two-letter name parts ("Al" in Al-Sayed) were not redacted | Name tokens of length ≥ 2 |
| 3 | GitHub usernames (e.g. `aferreira-dev`) identified candidates | Code links removed from scored text; kept for humans in `prep_report.json` |
| 4 | "900 ms" was flagged as the title "Ms" | Titles only match before a capitalised word |
| 5 | A model could quote the injection text as "evidence"; grounding passed because the text is in the CV | Validator rejects evidence containing injection text |
| 6 | Must-have gating could not tell "CV is silent" from "CV says they lack it" | New status `contradicted`; only it fails a gate |
| 7 | Equal scores were ordered by file name with no indication | Ties marked `=N` in ranking and report |
| 8 | The report was left to the model, so it could drift from the data | `render_report.py` renders it deterministically |
| 9 | The churn command listed deleted files and lockfiles (`poetry.lock`, old test paths) | Two-year window, existing files only, lockfiles/docs excluded |
| 10 | Small codebase: profile risked rewarding familiarity with ~2k lines of code | `repo-profile` now records gaps and says when the code is small |
| 11 | No guidance when the user can't answer planning questions | `hiring-plan` writes a draft brief with assumptions; rubric requires confirmation |

## Not yet verified

- Scoring by fresh, independent model sessions. The dry-run scores were produced in a single
  session by the same model that designed the fixture, so they show that the pipeline works,
  not how consistent or fair a model is. Run `evals/run_screening.sh` for that.
- Scanned (image-only) PDFs: detected and reported, but no OCR.
- Real-world CVs with complex layouts (columns, tables).
