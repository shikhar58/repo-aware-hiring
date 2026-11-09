# Responsible use

This plugin is **decision support** for software engineer hiring. It must not be used to make
automated hiring decisions.

## Design commitments

- **Human in the loop.** The rubric must be approved by a named person before scoring, and the
  report names the qualified person who reviews the results (or says none is recorded yet). Nothing is rejected or
  advanced automatically.
- **Redaction before scoring.** Names, contact details, profile and code links, age, nationality,
  photos and marital status are removed before the model scores a CV. A script blocks scoring
  until no such details remain, and the eval suite checks that name, gender and origin swaps
  produce identical redacted text.
- **Verifiable evidence.** A script rejects any score whose quoted evidence is not in the CV.
- **Independent scoring.** Each CV is scored alone against the rubric, which reduces order and
  anchoring effects between candidates.
- **Deterministic ranking.** Totals, gates and order are computed by `rank.py` and are reproducible.
- **Evidence or zero.** Every level must cite CV text; "no evidence" is reported as a gap to
  probe, not as a weakness.
- **Audit trail.** `rubric.json` (versioned, with approver), `redacted/`, `scores/` and
  `ranking.json` together show how every result was produced.

## Introduce it gradually

Start with a few roles where your team still reads every CV and compares its own shortlist with the
report before trusting the ranking. Keep humans reading CVs even then. There is no mode in which the
tool rejects candidates.

## Anthropic's Usage Policy

When this plugin runs on Claude, Anthropic's [Usage Policy](https://www.anthropic.com/aup) applies. From
12 November 2026 it treats employment, including "screening, ranking, advancing, or rejecting candidates; hiring", as a
**high-risk** use, for internal tools as well as customer-facing ones. Two requirements follow:

| Requirement | How the plugin supports it | What you must do |
|---|---|---|
| A qualified person meaningfully reviews each recommendation, has authority to change it, and stays responsible for the decision | Nothing is rejected or advanced automatically; the rubric needs a named approver; every score quotes the CV; `screen-candidates` asks who the qualified reviewer is and the report shows them, or says "not yet recorded" | Name a reviewer with the training or experience to judge the evidence, and have them read it before any decision |
| People who are the subject of a decision are clearly told AI was used | The job description draft has a placeholder for the notice and `check_jd.py` warns when a posting has none; `screen-candidates` asks whether candidates were told and the report says "not confirmed" until they are | Tell candidates, in the posting or separately, before any decision |

Drafting a job description or a codebase map is "internal drafting" that the policy excludes; screening and
ranking are not. The policy also prohibits discrimination on protected characteristics, inferring them from
biometric data, and inferring emotions: the plugin redacts protected details before scoring and its interview checks
block questions about them. Read the policy itself: this summary is not legal advice.

## Your obligations as a deployer (not legal advice)

Regulation of AI in recruitment varies by jurisdiction and changes often. Check current rules
with your legal team before use. Areas to review include:

- **EU AI Act:** AI systems used to screen or evaluate job applicants fall in the high-risk
  category; check which deployer obligations apply to you and from when.
- **GDPR (and UK GDPR):** lawful basis, candidate notice, data minimisation, retention limits,
  and Article 22 limits on solely automated decisions with significant effects.
- **US:** e.g. NYC Local Law 144 (bias audits and notice for automated employment decision tools),
  plus state laws in Illinois, Colorado and elsewhere.

## Data handling

- CVs and repo excerpts are sent to the model provider configured in your agent. Make sure that
  is permitted by your data-processing agreements and internal policies.
- Do not run this on repositories you are not authorised to share with that provider.
- Close each round when the role is filled or cancelled (`close-round`). It deletes extracted and
  redacted CVs, scores, rankings and reports (and the original CVs if you choose), and
  keeps an `audit.json` with pseudonymous ids, scores, gates and hashes only. `cleanup.py sweep
  --older-than <days>` lists rounds past your retention period. The retention period itself is your
  organisation's decision.
- Handle individual erasure requests by removing that candidate's files and re-ranking (see `close-round`).
- Tell candidates that AI-assisted screening is used and how to request human review.

## Known limitations

- Redaction patterns cover English, French, German, Spanish, Italian, Dutch and Portuguese labels.
  CVs in other languages depend on the agent's manual review.
- Candidate names are detected automatically but must be confirmed by the agent before scoring;
  a wrong confirmation would let a name through.

- CVs are a weak signal for engineering ability; use the interview probes and a work sample.
- Model scores can vary run to run; spot-check consistency by re-scoring a few CVs.
- Rubrics derived from one codebase can favour people who already know that stack. Use
  `transferable_from` generously.

## Test data

All CVs under `evals/fixtures/` are fictional. Names, employers and contact details are invented;
email addresses use `example.*` domains. Any resemblance to real people is coincidental.
