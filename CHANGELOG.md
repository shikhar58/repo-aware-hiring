# Changelog

All notable changes are listed here. The project follows [Semantic Versioning](https://semver.org/);
before 1.0, minor versions may change file formats.

## [0.5.0] — 2026-11-08

### Added
- **HTML report.** `render_report.py` now writes `report.html` next to `report.md`: summary tiles, a shortlist
  chart coloured by must-have status, a candidates × criteria heatmap, the rubric with weights, and a card per
  candidate with quoted evidence and interview probes. Filters, search, light/dark theme, mobile layout, and
  clean print-to-PDF. It is a single self-contained file: no network requests (enforced by a content security
  policy), and all CV-derived text is escaped. `--no-html` skips it.
- README redesign with visuals generated from the demo (`docs/assets/`), rendered as images so they also
  show in the GitHub mobile app.
- 4 new self-test checks (41 total): report.html exists, loads nothing from the network, has the CSP, and
  cannot be injected with markup from CV text.

### Fixed
- `close-round` now also deletes `report.html` (`--keep-report` keeps both report files).

## [0.4.2] — 2026-11-08

First version prepared for public release.

### Fixed
- **Names could reach the scorer.** Redaction assumed the first line of a CV is the name, so a CV
  starting with "Curriculum Vitae" kept the real name, and the checker passed it. Names are now
  detected from the top lines (skipping headings and job titles), stored in `identities.json`, and must
  be confirmed or corrected by the agent; `check_redaction.py` fails until they are.
- **Only English was covered.** Date of birth, age, nationality, marital status, gender and religion
  labels are now detected in French, German, Spanish, Italian, Dutch and Portuguese, as are common
  prompt-injection phrases. Other languages rely on the agent's review, as the skill now states.
- **Numbers were redacted as phone numbers.** "12 000 000 users" or a year range in brackets became
  `[PHONE]`. Phone detection now uses the surrounding line: contact lines and `+` prefixes are redacted,
  thousands-grouped numbers, dates and bare IDs in prose are kept.
- Re-running `prepare_cvs.py` no longer overwrites redacted files edited by hand (`--force` to override).

### Added
- `identities.py` to list, confirm and correct candidate names.
- Redaction regression fixture (`evals/fixtures/redaction/`) and 17 new self-test checks (37 total).
- LICENSE (MIT), SECURITY.md, this changelog. CI tests Python 3.10, 3.12 and 3.13 with actions pinned
  to commit SHAs.

### Removed
- `shadow-pilot` skill (kept as an idea for a later release).

## [0.4.0]

- Marketplace file, plugin icon, two-minute demo, CI workflow.
- `close-round` skill: deletes candidate data, keeps a pseudonymous `audit.json`, sweeps overdue rounds.

## [0.3.0]

- Dry run on a public repo; deterministic guardrails (`prepare_cvs`, `check_redaction`,
  `validate_scores`, `rank`, `render_report`); eval harness with counterfactual fairness checks.

## [0.2.0]

- `hiring-plan` skill for planning a hire with follow-up questions and role designs.

## [0.1.0]

- `repo-profile`, `hiring-rubric` and `screen-candidates` skills.
