# repo-aware-hiring

> **Status: beta.** Decision support, not yet validated at scale. It never rejects anyone;
> humans read the CVs and decide. See [what has and hasn't been verified](docs/DRY_RUN.md).

**Repo-aware decision support for software engineer hiring.** Runs inside your own coding agent
(Claude Code, or any agent that supports Agent Skills), next to your codebase. Your code and
candidate data go to the model provider you already use, not to a separate hiring vendor.

Instead of matching CV keywords against a generic job description, it first works out what the
hire is for and what your codebase actually demands, turns that into a rubric a human approves,
then screens CVs against it with evidence quoted from each CV.

```
your need ──► hiring-plan ──► brief.md
                                 │
repo ───────────────────────► repo-profile ──► hiring-rubric ──(human approves)──► screen-candidates ──► report.md
JD (optional) ─────────────────────────────────────┘                     CVs ───────────┘
```

See [`docs/example-report.md`](docs/example-report.md) for real output from a dry run.

## Try it in 2 minutes (no model, no setup)

```bash
git clone https://github.com/shikhar58/repo-aware-hiring.git && cd repo-aware-hiring
python3 demo/run_demo.py        # needs pdftotext (poppler-utils) for the PDF CVs
open hiring/demo/report.md
```

The demo runs the real pipeline on 12 synthetic CVs (Markdown, PDF and DOCX, including a hidden
prompt injection) and uses scores recorded during the dry run in place of the model.

## Install

In Claude Code:

```
/plugin marketplace add shikhar58/repo-aware-hiring
/plugin install repo-aware-hiring@repo-aware-hiring
```

Or from a shell: `claude plugin marketplace add shikhar58/repo-aware-hiring` then
`claude plugin install repo-aware-hiring@repo-aware-hiring`.
Requires Python 3.10+ and `pdftotext` (poppler-utils) for PDF CVs.

## Skills (v0.4)

| Skill | What it does | Output |
|---|---|---|
| `hiring-plan` | Asks follow-up questions one at a time, investigates the relevant part of the repo, proposes 2–3 role designs, writes an approved brief | `brief.md` |
| `repo-profile` | Samples the codebase in the brief's scope: stack, architecture, conventions, gaps, hard problems | `repo-profile.md` |
| `hiring-rubric` | Turns brief + JD + profile into weighted criteria with observable anchors; waits for approval | `rubric.json` |
| `screen-candidates` | Redacts CVs, scores each one alone with verbatim evidence, validates, ranks and renders the report | `scores/`, `ranking.json`, `report.md` |
| `close-round` | Deletes candidate data when the role closes; keeps a pseudonymous audit record; finds overdue rounds | `audit.json` |

## What is deterministic

The model plans, profiles, drafts the rubric and scores. Everything that can be code is code
(standard-library Python in `skills/screen-candidates/scripts/`):

| Script | Job |
|---|---|
| `prepare_cvs.py` | Assign ids, extract text (PDF via `pdftotext`, DOCX, MD, TXT), first-pass redaction (EN, FR, DE, ES, IT, NL, PT), injection scan |
| `identities.py` | Confirm or correct each detected candidate name; scoring is blocked until every name is confirmed |
| `check_redaction.py` | Block scoring if a name is unconfirmed, or if names, contact details, age, nationality or links remain |
| `validate_scores.py` | Schema and consistency checks; every evidence quote must appear in the CV; injection CVs must be flagged |
| `rank.py` | Weighted totals, must-have gates, ties; refuses invalid scores |
| `render_report.py` | Builds `report.md` from the data |

## Workspace layout

One folder per role, inside the repo you are hiring for. Add `hiring/` to `.gitignore`.

```
hiring/db-owner/
├── brief.md            # hiring-plan, approved by you
├── jd.md               # optional; can be drafted from the brief
├── repo-profile.md     # repo-profile
├── rubric.json         # hiring-rubric, approved by you
├── cvs/                # you provide
├── candidates.json     # id → file
├── identities.json     # id → confirmed name (personal data)
├── extracted/          # raw text: personal data, delete when the round closes
├── redacted/           # what the model scores
├── prep_report.json    # extraction problems, injection hits, code links (for humans)
├── scores/             # one file per candidate
├── ranking.json
├── report.md
├── round.json          # opened/closed dates (retention)
└── audit.json          # written when the round is closed
```

## Usage

```
> I want to hire someone to own the database layer of this repo
  (a few questions, a look at the code, 2–3 role designs, a brief)
> Profile the repo for db-owner
> Build the rubric for db-owner        (review, edit, approve)
> Screen the candidates for db-owner
> Close the db-owner round              (preview, confirm, delete)
```

## Using it responsibly

Start with a few roles where your team still reads every CV and compares its own shortlist with
the report. Treat the ranking as a second opinion. The tool never rejects anyone.

## Evals

```bash
python3 evals/selftest.py      # 37 deterministic checks, no model; runs in CI
```

Model evals for consistency, counterfactual fairness and injection resistance run against a
fixture with 12 synthetic CVs and generated name/gender/origin/university/career-break variants.
See [`evals/README.md`](evals/README.md).

## Design principles

- **Plan before screening.** The mission and the code decide the criteria, not a keyword list.
- **Rubric first.** No candidate is scored until a named human approves the rubric.
- **Evidence or zero.** Every level quotes the CV; the validator checks the quote exists.
- **Silent ≠ lacking.** "No evidence" is a gap to probe; only an explicit contradiction fails a must-have.
- **Independent scoring** against redacted text; candidates are never compared while scoring.
- **CVs are untrusted.** Injection attempts are detected, flagged and ignored.
- **Names are confirmed, not guessed.** Redaction is only as good as knowing whose CV it is.

Read [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md) before using this with real candidates, and
[`docs/DRY_RUN.md`](docs/DRY_RUN.md) for what has and hasn't been verified.

## Roadmap

- Run model evals across several fresh sessions and publish the results
- `interview-kit`, `take-home-gen`, `take-home-grade`, `debrief` skills
- Backtesting on past hiring rounds and company-specific calibration
- OCR for scanned PDFs

## Security

Found a way to get personal data past redaction, or to move a score with text in a CV? Please
report it privately: see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
