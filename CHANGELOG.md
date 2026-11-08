# Changelog

All notable changes are listed here. The project follows [Semantic Versioning](https://semver.org/);
before 1.0, minor versions may change file formats.

## [0.8.0] — 2026-11-08

### Added
- **`map-codebase` skill.** Builds `hiring/_repo/codebase-map.md`, a whole-system map with file citations in 13
  sections: overview, components and services, data stores and schema, APIs and integrations, authentication and
  security, CI/CD, deployment and infrastructure, observability, testing, dependencies, conventions, hot spots and
  risks (INTERNAL, never published) and gaps.
- **`inventory.py`.** Deterministic scan of languages, manifests, packages, compose services, containers, pipelines,
  deployment and IaC files, migrations and schema, API specs, auth and security code and tooling, data stores, queues,
  ORMs, proxies, observability and test frameworks. Lists env files without reading them. Records a fingerprint and
  per-file hashes of the structurally important files.
- **`check_map.py` gate.** Fails when a section is missing or cites nothing, a cited path doesn't exist, anything the
  inventory found isn't explained, the risks section isn't marked INTERNAL, a secret was copied in, or the map is stale
  (naming the changed files).
- Example map of the FastAPI template (`docs/example-codebase-map.md`), a synthetic mini-repo fixture, and new
  self-test checks.

### Changed
- `hiring-plan`, `repo-profile`, `write-job-description`, `hiring-rubric`, `screen-candidates` and `interview-kit` now run
  the map gate first and refuse to start on a missing or stale map. `repo-profile` builds on the map instead of sampling.
- `check_jd.py` (and so `validate_kit.py`) treats every path named in the map as internal.

## [0.7.0] — 2026-11-08

### Added
- **`interview-kit` skill.** Structured interview kits per candidate: core questions shared by everyone (one or more per
  must-have and important criterion, grounded in the repo's real problems and phrased safely for candidates) plus
  personal questions from each CV (deep dives into quoted claims, probes for must-haves the CV didn't show,
  neutral consistency questions). Each question has follow-ups, strong-answer signals, warning signs and minutes.
- **`validate_kit.py`.** Requires core coverage of every must-have, a personal probe for every unshown must-have,
  quoted claims that are really in the CV, and a fit within the interview length; blocks leaked internals (shared with
  `check_jd.py`) and questions about protected characteristics, without flagging terms like "race condition".
- **`render_kit.py`.** Printable, self-contained HTML kits with a time plan and a 0–3 scorecard using the rubric's
  anchors, plus Markdown and an index page.
- Demo step 7 renders kits for three candidates. 13 new self-test checks (71 total).

### Changed
- `close-round` deletes `interviews/`. `screen-candidates` offers interview kits after the report.
- `check_jd.py` exposes `find_leaks()` for reuse.

## [0.6.0] — 2026-11-08

### Added
- **`write-job-description` skill.** Writes a public job posting from the repo and a question-and-answer session
  with the hiring manager (one question at a time; reuses the hiring brief when there is one). Translates repo
  findings into public language, drafts section by section, and keeps must-haves consistent with the rubric.
- **`check_jd.py`.** Blocks internal details in a posting (file paths, names from the repo profile and brief,
  environment variables, IPs, internal hosts, credentials, stated security weaknesses) and warns about gendered,
  age-coded and exclusionary wording, years-of-experience and degree demands, "native speaker", long must-have
  lists, a missing pay range, missing sections, and must-haves that drift from the rubric.
- Example posting for the demo role (`docs/example-jd.md`), a bad-posting fixture, and 17 self-test checks (58 total).

### Changed
- `hiring-plan` and `hiring-rubric` hand off to `write-job-description`; the README flow diagram includes it.

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
