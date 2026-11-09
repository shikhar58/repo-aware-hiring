# Changelog

All notable changes are listed here. The project follows [Semantic Versioning](https://semver.org/);
before 1.0, minor versions may change file formats.

## [0.13.2] — 2026-11-09

### Removed
- README "Status and roadmap" section. The beta status stays in the badges, and what has been verified is linked
  from "Going further".

 — 2026-11-09

### Changed
- README: the comparison posting is now an ordinary, realistic one (6 warnings) instead of a caricature.
- The tagline "Candidates see the work, never the code" is now "Candidates learn precisely what the role requires,
  without your codebase being revealed", in the README, privacy diagram, walk-through and social card.

 — 2026-11-09

### Added
- `scripts/install.sh`: installs the skills by copying them, with no network access or Node:
  `--agents` (Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode and others, into `.agents/skills/`), `--claude`
  (`.claude/skills/`), `--global` for every project, `--dir PATH`, and `--remove`. It updates its own earlier
  installs and never overwrites a different skill with the same name. Five new self-test checks.
- README: the script as a third install option.

 — 2026-11-09

### Changed
- **Agent-neutral skills.** Every `SKILL.md` refers to scripts by paths relative to its own folder (and
  `../<skill>/` for a sibling skill) instead of Claude Code's `${CLAUDE_PLUGIN_ROOT}`, and says where shared scripts
  live. The skills work in any agent that supports the Agent Skills standard; Claude Code can still install them
  as a plugin.
- README: presents the skills for any coding agent, with install instructions for Claude Code and for Codex, Cursor,
  Gemini CLI, GitHub Copilot and others (`npx skills add shikhar58/repo-aware-hiring --skill '*'`). The social preview
  card matches.

### Added
- CI job that validates every skill with the Agent Skills reference validator (`skills-ref` 0.1.5).

### Fixed
- In a repository with no commits yet, the inventory recorded the commit as "HEAD" instead of none.

 — 2026-11-09

Aligned with Anthropic's plugin directory requirements and its Usage Policy, which from 12 November 2026 treats
screening and ranking candidates as a high-risk use.

### Added
- **Human review and candidate notice.** `screen-candidates` asks who the qualified reviewer is and whether
  candidates were told AI is used, and records both. The report shows the reviewer and the notice status, or says
  "not yet recorded" / "not confirmed". The disclaimer now says a qualified person must review each candidate, can
  change any result and is responsible for the decision.
- `check_jd.py` warns when a posting doesn't tell candidates that AI helps screen them; the placeholder explains why
  the notice is required.
- `PRIVACY.md`, and an Anthropic Usage Policy section in `docs/COMPLIANCE.md`.
- Directory listing fields in `plugin.json`: `displayName`, `icon`, `documentationUrl`, `supportUrl`,
  `privacyPolicyUrl`.

### Changed
- Plugin and marketplace descriptions describe the plugin as decision support with human review.
- The README's typical posting now gets 10 warnings, including the missing AI notice.

 — 2026-11-09

### Added
- Issue templates: "Tell us about your hiring round" (feedback) and a bug report; both remind people not to paste
  candidate data or internal code. Security reports go to SECURITY.md.
- README "Support the project" section, and a 1280×640 social preview image (`docs/assets/social-preview.png`).

### Changed
- README says plainly that it is built for and tested with Claude Code; other agents that load Agent Skills may work
  but are untested. The inventory speed claim is now measured: about two seconds on Ollama's 380,000 lines of Go.
- The intro names what people search for: Claude Code plugin, job descriptions, CV and résumé screening, technical
  interview questions.

 — 2026-11-09

### Changed
- The README's before/after now uses Ollama (about 380,000 lines of Go): a posting for a Senior Software Engineer,
  Inference Engine, drafted with a focus on new model support. Full draft in `docs/example-ollama-jd.md`; the mem0
  example page is removed. The comparison posting and the animated walk-through match the new example.

 — 2026-11-09

### Changed
- **README rewritten for new users.** It leads with the job description (the easiest place to start), says who it
  is for and who it isn't for, shows a before/after on mem0's public code (an unofficial example), and puts install
  and the demo near the top. An animated walk-through shows a real session. It is about 500 lines instead of 660.
- In-depth material moved to `docs/GUIDE.md` (codebase map, several repos, focus prompt, questions and decisions),
  `docs/REFERENCE.md` (skills, scripts, files, design principles) and `docs/SAFEGUARDS.md`.
- New example: `docs/example-mem0-jd.md`, the full draft posting.

### Fixed
- `check_jd.py` now flags a degree listed under must-haves (even without "required" next to it), school pedigree
  ("top university", "IIT", "Ivy League"), and must-have lists longer than 5, as the README says. Previously it
  allowed six.
- The sample planning conversation no longer has the agent recommend a role design.

 — 2026-11-09

### Added
- README: **"Your code stays private"** section with a diagram. Candidates see the work, never the code, and your
  code goes nowhere it doesn't already go, because everything runs inside the coding agent your team already uses.
  Also a tagline under the intro and two comparison rows ("Who sees your code", "What candidates see").

### Fixed
- In single-repo mode nothing kept `hiring/` out of git, so CVs could be committed by accident. The first step that
  creates it (the inventory, or `prepare_cvs.py`) now writes `hiring/.gitignore` ignoring everything inside,
  without touching the repo's own `.gitignore`.

 — 2026-11-08

### Changed
- **No pre-selected answers, and every question can be skipped.** Questions list their options with nothing chosen
  or marked as a default, followed by "Write my own answer" and "Skip".
- **A skip is recorded as none** (`decisions.py add … --skipped`), and so is a question nobody answers. Nothing is
  guessed in its place: each stage works from what is known and says what it did without the answer (a placeholder
  in the job description, no scope weights in the rubric, no shortlist cut-off, one interviewer). A skip never
  approves the rubric or deletes data. `check_ready.py` shows each stage what was skipped; `decisions.py pending`
  lists skipped questions to answer later.
- Checkpoints no longer show a plan of defaults to "approve all", and no longer record assumed defaults for
  unattended runs.

 — 2026-11-08

### Changed
- **Follow-up questions** follow one rule in every skill ([How to ask a question](skills/hiring-workspace/CHECKPOINTS.md#how-to-ask-a-question)):
  options are never labelled "recommended" (the option the evidence supports goes first, with its reason in neutral
  words), and there is always a last option to write your own answer. Checkpoint plans show defaults without
  calling them recommended. A self-test keeps "recommended" labels out of the skills.

 — 2026-11-08

### Changed
- `write-job-description` produces a **draft for the hiring manager**, marked as one at the top. It writes only
  what the code, the brief or the manager's answers support; pay, location details, hiring steps, timeline, benefits
  and the equal opportunity statement are `[insert: …]` placeholders unless the manager gave them. "How we hire" holds
  no generic text: just placeholders for the steps and for how AI-assisted screening is disclosed.
- The "Backgrounds we welcome" section is no longer in the draft; managers can add it.
- `check_jd.py` lists every placeholder (ignoring HTML comments) and accepts a pay-range placeholder instead of
  warning about a missing range.

 — 2026-11-08

### Changed
- Job descriptions no longer have an "Our stack" section. Companies rarely want to publish their exact stack, so the
  technologies show through the work ("tune keyword and vector search") and through must-haves and nice-to-haves as
  examples among alternatives ("vector databases such as Qdrant, pgvector or Elasticsearch"). `check_jd.py` warns
  when a posting has a stack section; keep one only if the hiring manager decides to publish it.

 — 2026-11-08

Found by running the job-description pipeline on a large real monorepo (mem0: ~230k lines, 25 packages, 34 pipelines).

### Fixed
- The inventory treated placeholder URLs in tests, examples and docs (`http://x`, `http://my-host:1234`) as internal
  service calls, flooding the map gate with warnings (28 hosts on mem0, 3 after the fix).
- The focus version stamp was visible in the public job posting. Public outputs now carry it in an HTML comment.

 — 2026-11-08

### Added
- **Multi-repo workspaces (`hiring-workspace` skill).** A private folder outside the repos that references local
  checkouts or clones git URLs (URLs with credentials are refused; a workspace inside a repo is refused).
  `workspace.py` creates it, adds repos, sets tiers (primary, supporting, ignored), scans, syncs, shows status and
  starts roles. Single-repo use is unchanged.
- **Cross-repo graph.** `inventory.py` now records what each repo publishes and depends on, which container images it
  builds and deploys, Kubernetes and compose service names, internal hosts it calls, and API contracts (output only:
  existing map fingerprints are unchanged). `system_graph.py` turns that into links between repos (package, image,
  HTTP, shared contract), groups repos built from one template, and lists internal hosts it can't match.
- **Tiered maps and a system map.** Primary repos need a full map; supporting repos a shorter service card
  (`check_map.py --level card`). `check_system.py` requires every repo to be mapped at its tier and
  `system/system-map.md` to describe every repo, explain every link and name template groups, and goes stale when
  repos, tiers or links change.
- **Focus prompt per role** (`focus.md`). Every stage reads it; outputs record its version and `focus.py stale` lists
  what to redo after a change. It rejects criteria about people (age, gender, origin, religion, family, health,
  schools, appearance) and attempts to switch off safeguards, without flagging terms like "race condition" or
  "React Native".
- **`trace_usage.py`.** Where a library is defined, which repos declare it (and at which versions), every import and
  call site per symbol, and public symbols nobody uses. Python, TypeScript/JavaScript, Go, Java/Kotlin.
- **Planning checkpoints** at every stage ([`CHECKPOINTS.md`](skills/hiring-workspace/CHECKPOINTS.md)): at most three
  decisions with recommended defaults, "approve all" or change one item, a decisions log (`decisions.py`) so nothing
  is asked twice, and recorded assumptions when nobody is there to answer.
- **`check_ready.py`**, one gate for every skill in either mode: maps, system map, focus and decisions.
- **Interview panels.** Optional `panel` in `core.json`: each interviewer owns criteria; kits show who asks what and
  a panel table; `validate_kit.py` checks that every core question has an interviewer and fits their slot.
- **Scope weights.** Optional `scope` (share of the work per repo) and per-criterion `repos` in `rubric.json`,
  checked by `rank.py` and shown in the report with the focus version.
- Multi-repo fixture, example system map (`docs/example-system-map.md`), system-map diagram, and 41 new self-test
  checks (126 total).

### Changed
- All skills run `check_ready.py` instead of `check_map.py`, then a planning checkpoint for their stage.
- `check_jd.py` (and so `validate_kit.py`) also treats workspace maps, the focus, and distinctive repo and package
  names as internal.
- `close-round` keeps `focus.md` and `decisions.json` for the next round.

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
