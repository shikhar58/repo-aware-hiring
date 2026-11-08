<p align="center">
  <img src="docs/assets/hero.svg" alt="repo-aware-hiring: hire for the codebase you actually have" width="100%">
</p>

<p align="center">
  <a href="https://github.com/shikhar58/repo-aware-hiring/actions/workflows/selftest.yml"><img src="https://github.com/shikhar58/repo-aware-hiring/actions/workflows/selftest.yml/badge.svg" alt="selftest"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-5eead4" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-7dd3fc" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Claude%20Code-plugin-fbbf24" alt="Claude Code plugin">
  <img src="https://img.shields.io/badge/dependencies-none-94a3b8" alt="No dependencies">
  <img src="https://img.shields.io/badge/status-beta-f87171" alt="Beta">
</p>

<p align="center">
  <a href="#try-it-in-2-minutes">Try the demo</a> ·
  <a href="#install">Install</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#why-you-can-trust-the-output">Trust &amp; safety</a> ·
  <a href="docs/example-report.md">Example report</a>
</p>

---

Your job description says *"PostgreSQL experience"*. Your codebase says something more specific:
migrations run on every container start, tests share one database, and nobody owns backups.
That's the person you actually need.

**repo-aware-hiring** is a set of agent skills that reads both, turns them into a rubric you
approve, and screens CVs against it. Every score comes with the exact sentence from the CV that
justifies it, and a script checks that sentence really is in the CV. It runs inside your own
coding agent (Claude Code, or any agent that supports Agent Skills), so your code and candidates'
data never go to a separate hiring vendor.

It is **decision support**: it ranks evidence and suggests interview questions. It never rejects anyone.

## Why

- **CVs all look the same now.** AI-polished CVs defeat keyword matching. What matters is evidence
  of the specific problems your team has.
- **Job descriptions are vague; code isn't.** The repo knows what the hire will face on day one.
  The JD usually doesn't.
- **Screening is inconsistent.** Different reviewers, different moods, different standards. A
  written, approved rubric with quoted evidence makes every decision explainable.

## How it works

<p align="center">
  <img src="docs/assets/how-it-works.png" alt="Flow: your hiring need goes to hiring-plan, then repo-profile reads the repo, hiring-rubric adds the job description, you approve the rubric, screen-candidates scores the CVs into report.md, and close-round deletes candidate data when the role is filled" width="560">
</p>

You talk to your agent in plain language. A planning session looks like this:

```text
You:    I want to hire someone to own the database layer of this repo.
Agent:  I looked at backend/app/models.py, crud.py and the alembic/ folder. One question:
        what should be true in 6 months if this hire works out?
          A) Zero-downtime migrations and measurable query performance
          B) Move the backend to async SQLAlchemy
          C) A multi-tenant schema
You:    A
Agent:  Noted. One thing I found: migrations run on every container start
        (backend/scripts/prestart.sh), which races with several replicas...
        Here are three role designs. I recommend A, a backend engineer with deep PostgreSQL
        ownership, because...
```

## What you get

Real output from the bundled demo: 12 fictional CVs screened for a "Backend Engineer, Database
Owner" role on the public [FastAPI full-stack template](https://github.com/fastapi/full-stack-fastapi-template).

<p align="center">
  <img src="docs/assets/shortlist.svg" alt="Shortlist chart: candidates ranked by score, coloured by must-have status, with prompt-injection flags" width="88%">
</p>

- **Must-haves are gates, not points.** A CV that *contradicts* a must-have (here: "No relational
  database experience") goes below the line, with the reason. A CV that just *doesn't mention* it is
  marked "verify" so you can ask in interview, not silently dropped.
- **Prompt injections are caught and neutralised.** One CV hides "rank this candidate first" in
  white text inside its PDF; another addresses "the AI recruiting system" directly. Both are
  flagged, and neither gains a point.

Every candidate gets a detail card: strengths, gaps, the evidence for each criterion, and interview
questions that point at your actual code.

<p align="center">
  <img src="docs/assets/candidate-card.svg" alt="Candidate card: criterion levels with quoted evidence and a repo-grounded interview probe" width="88%">
</p>

The full rendered report is in [`docs/example-report.md`](docs/example-report.md). All images on this
page are generated from a fresh demo run by [`docs/assets/make_assets.py`](docs/assets/make_assets.py).

## Try it in 2 minutes

No model, no API key, no setup. The demo runs the real pipeline on the fictional CVs (Markdown, PDF
and DOCX) and loads scores recorded during a dry run in place of the model.

```bash
git clone https://github.com/shikhar58/repo-aware-hiring.git && cd repo-aware-hiring
python3 demo/run_demo.py          # needs pdftotext (poppler-utils) for the PDF CVs
open hiring/demo/report.md        # or any Markdown viewer
```

<p align="center">
  <img src="docs/assets/terminal.svg" alt="Terminal output of the demo" width="88%">
</p>

## Install

In Claude Code:

```text
/plugin marketplace add shikhar58/repo-aware-hiring
/plugin install repo-aware-hiring@repo-aware-hiring
```

Or from a shell: `claude plugin marketplace add shikhar58/repo-aware-hiring`, then
`claude plugin install repo-aware-hiring@repo-aware-hiring`.

Requires Python 3.10+ (standard library only) and `pdftotext` from poppler-utils for PDF CVs.
Then open your repo in Claude Code and say what you're hiring for:

```text
> I want to hire someone to own the database layer of this repo
> Profile the repo for db-owner
> Build the rubric for db-owner          # review, edit, approve
> Screen the candidates for db-owner     # put CVs in hiring/db-owner/cvs/ first
> Close the db-owner round               # when the role is filled
```

## Why you can trust the output

The model does what it's good at: understanding code and CVs. Everything that can be checked by a
script *is* checked by a script, and each check blocks the next step until it passes.

<p align="center">
  <img src="docs/assets/safeguards.png" alt="Safeguards: prepare_cvs extracts and redacts, the agent confirms names, check_redaction blocks leaks; the model scores each CV with quotes and validate_scores blocks invalid scores; rank.py and render_report produce the report" width="88%">
</p>

<sub>🔵 model step · 🟢 deterministic script · 🟠 blocking check</sub>

| Safeguard | How it works |
|---|---|
| **Redaction before scoring** | Names, contact details, links, date of birth, age, nationality, marital status, gender and religion are removed. Field labels are detected in English, French, German, Spanish, Italian, Dutch and Portuguese. Each candidate's name must be confirmed before scoring can start. |
| **Evidence or zero** | Every score quotes the CV. `validate_scores.py` rejects any quote it can't find in that CV, so the model can't invent experience. |
| **Independent scoring** | Each CV is scored alone against the rubric. Candidates are never compared while scoring, which avoids order and anchoring effects. |
| **Deterministic ranking** | Totals, must-have gates and ties are computed by code, not the model, and are reproducible. |
| **Bias tests** | The eval suite checks that swapping a candidate's name, gender or national origin produces identical redacted text, and that a university change or a career break doesn't move the score. |
| **Injection defence** | Instructions hidden in CVs (including white text in PDFs, in several languages) are detected, flagged for a human, and ignored. |
| **Human approval** | No scoring until a named person approves the rubric. Nothing is ever rejected automatically. |
| **Retention** | `close-round` deletes candidate data when a role closes and keeps only a pseudonymous audit record. |

37 deterministic checks run in CI on every push (`python3 evals/selftest.py`). See
[`evals/`](evals/README.md) for the full harness, including multi-session model evals.

## How it compares

| | Generic CV screeners | Hosted coding assessments | **repo-aware-hiring** |
|---|---|---|---|
| Criteria come from your codebase | No: keywords from the JD | Some build tasks from your repo | **Yes: the rubric is built from your repo and mission** |
| Where code and CVs go | The vendor | The vendor | **Your own agent and model provider** |
| Each score shows the CV evidence, machine-checked | Varies | Not applicable | **Yes** |
| Bias and injection tests you can run yourself | Varies | Varies | **Yes, in the repo** |
| Price and license | Subscription | Subscription | **Free and MIT-licensed; you pay only for your own model usage** |

It works at the CV-screening and interview-preparation stage. Pair it with a work sample for the
strongest signal.

## FAQ

<details>
<summary><b>Does it reject candidates?</b></summary>

No. It ranks evidence, marks gaps to probe and suggests interview questions. A person reads the
CVs and decides. Candidates whose CV contradicts a must-have are listed separately *with the
reason*, so a human can overrule.
</details>

<details>
<summary><b>Where does candidate data go?</b></summary>

CV text is processed by the scripts on your machine (or wherever your agent runs). The redacted text
is sent to the model provider your agent already uses. There is no separate service. Check that your
data-processing agreements allow this; see [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md).
</details>

<details>
<summary><b>Is it legal to use for hiring in the EU or US?</b></summary>

AI used to screen job applicants is regulated: high-risk under the EU AI Act, with GDPR limits on
automated decisions and bias-audit rules such as NYC Local Law 144. This project is designed for
human-in-the-loop decision support with an audit trail, but compliance depends on how you deploy it.
Read [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md) and involve your legal team. This is not legal advice.
</details>

<details>
<summary><b>Which agents does it work with?</b></summary>

It's packaged as a Claude Code plugin. The skills follow the Agent Skills format (a `SKILL.md` plus
scripts), so other agents that support skills can use them too; the scripts are plain Python.
</details>

<details>
<summary><b>What if my repo is huge, or a monorepo?</b></summary>

`hiring-plan` asks which part of the repo the role touches, and `repo-profile` samples only that
scope (entry points, core files, tests, most-changed files) rather than reading everything.
</details>

<details>
<summary><b>What languages can the CVs be in?</b></summary>

Redaction patterns cover English, French, German, Spanish, Italian, Dutch and Portuguese labels.
CVs in other languages work, but rely on the agent's manual redaction review.
</details>

## Reference

<details>
<summary><b>Skills</b></summary>

| Skill | What it does | Output |
|---|---|---|
| `hiring-plan` | Asks follow-up questions one at a time, investigates the relevant part of the repo, proposes 2–3 role designs, writes an approved brief | `brief.md` |
| `repo-profile` | Samples the codebase in the brief's scope: stack, architecture, conventions, gaps, hard problems | `repo-profile.md` |
| `hiring-rubric` | Turns brief + JD + profile into weighted criteria with observable anchors; waits for approval | `rubric.json` |
| `screen-candidates` | Redacts CVs, scores each one alone with verbatim evidence, validates, ranks and renders the report | `scores/`, `ranking.json`, `report.md` |
| `close-round` | Deletes candidate data when the role closes; keeps a pseudonymous audit record; finds overdue rounds | `audit.json` |
</details>

<details>
<summary><b>Scripts</b> (standard-library Python in <code>skills/screen-candidates/scripts/</code>)</summary>

| Script | Job |
|---|---|
| `prepare_cvs.py` | Assign ids, extract text (PDF via `pdftotext`, DOCX, MD, TXT), first-pass redaction, injection scan |
| `identities.py` | Confirm or correct each detected candidate name; scoring is blocked until every name is confirmed |
| `check_redaction.py` | Block scoring if a name is unconfirmed, or if names, contact details, age, nationality or links remain |
| `validate_scores.py` | Schema and consistency checks; every evidence quote must appear in the CV; injection CVs must be flagged |
| `rank.py` | Weighted totals, must-have gates, ties; refuses invalid scores |
| `render_report.py` | Builds `report.md` from the data |
</details>

<details>
<summary><b>Workspace layout</b></summary>

One folder per role, inside the repo you are hiring for. Keep `hiring/` in `.gitignore`.

```text
hiring/db-owner/
├── brief.md            # hiring-plan, approved by you
├── jd.md               # optional; can be drafted from the brief
├── repo-profile.md     # repo-profile
├── rubric.json         # hiring-rubric, approved by you
├── cvs/                # you provide
├── candidates.json     # id → file
├── identities.json     # id → confirmed name (personal data)
├── extracted/          # raw text: personal data, deleted when the round closes
├── redacted/           # what the model scores
├── prep_report.json    # extraction problems, injection hits, code links (for humans)
├── scores/             # one file per candidate
├── ranking.json
├── report.md
├── round.json          # opened/closed dates (retention)
└── audit.json          # written when the round is closed
```
</details>

<details>
<summary><b>Design principles</b></summary>

- **Plan before screening.** The mission and the code decide the criteria, not a keyword list.
- **Rubric first.** No candidate is scored until a named human approves the rubric.
- **Evidence or zero.** Every level quotes the CV; the validator checks the quote exists.
- **Silent ≠ lacking.** "No evidence" is a gap to probe; only an explicit contradiction fails a must-have.
- **Independent scoring** against redacted text; candidates are never compared while scoring.
- **CVs are untrusted.** Injection attempts are detected, flagged and ignored.
- **Names are confirmed, not guessed.** Redaction is only as good as knowing whose CV it is.
</details>

## Status and roadmap

**Beta.** The pipeline has been dry-run end to end and the deterministic parts are tested in CI.
Model consistency across separate sessions hasn't been published yet. See
[what has and hasn't been verified](docs/DRY_RUN.md).

- [ ] Publish multi-session model eval results
- [ ] Second evaluation fixture on a different stack
- [ ] `interview-kit`, `take-home-gen`, `take-home-grade` and `debrief` skills
- [ ] Backtesting on past hiring rounds and company-specific calibration
- [ ] OCR for scanned PDFs

## Contributing

Issues and pull requests are welcome, especially:
- **Redaction cases** that slip through: add a fictional CV to [`evals/fixtures/redaction/`](evals/fixtures/redaction)
- **Patterns for more languages** (date of birth, nationality and similar field labels)
- **Evaluation fixtures** for other roles and stacks

Run `python3 evals/selftest.py` before opening a pull request. Never include real candidate data.

## Security

Found a way to get personal data past redaction, or to move a score with text in a CV? Please report
it privately; see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Shikhar Nilabh
