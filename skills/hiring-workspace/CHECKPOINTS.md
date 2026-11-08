# Planning checkpoints

Every stage starts with a short planning checkpoint, so the hiring manager steers the work where their knowledge
matters, and nothing they already answered is asked again. Each skill's own `## Planning checkpoint` section
lists the decisions for its stage; this file says how to run one.

## How to ask a question

Every follow-up question, in every skill, follows the same shape:

- **Multiple choice, one question at a time**, with 2–4 concrete options drawn from the code, the brief or earlier
  answers. Use the question tool when there is one.
- **Nothing is chosen for them.** No option is pre-selected, marked as a default, or labelled "recommended" (nor
  "best" or "suggested"). Each option's description says, in neutral words, what it is based on ("Matches the two
  hardest problems in the profile").
- **After all the options, always two more:** "Write my own answer" and "Skip". If the question tool already adds a
  free-text choice of its own (such as "Other"), that is the write-your-own option: don't show it twice. In plain
  text, end the list with "Or write your own answer, or skip."
- When several options can apply together, allow choosing more than one; the write-your-own and skip options stay.

## Skipped means none

A skipped question, or one nobody answers (the person is away, or the session runs unattended), is recorded as
**none**: `decisions.py add <folder> --stage <stage> --key <key> --skipped`. Nothing is guessed in its place.
Every stage then works from what is actually known and leaves the rest open:

- in a **public draft** (the job description), the missing fact becomes an `[insert: …]` placeholder;
- in **internal work** (profile, rubric, screening, kits), the step uses only the code, the focus and the
  answers it has, and says in one line what it did without the skipped answer (the "if none" column below);
- anything that needs a person's approval (the rubric, deleting data) still waits for that person: a skip never
  approves anything.

A skipped decision can be answered later; record the answer and redo the outputs that depend on it.

## How to run a checkpoint

1. **Run the gate first.** `check_ready.py <repo-or-workspace> --role <role> --stage <stage>` prints what is
   already decided for this stage, including what was skipped.
2. **Reuse what is decided.** Never re-ask a recorded decision, including a skip, unless the person brings it up.
   Name it in one line ("Using the scope you set on 8 Nov: payments-lib 50%, checkout-svc 30%, billing-svc 20%";
   "Pay range was skipped, so the draft keeps a placeholder").
3. **Ask the stage's questions** (at most three), one at a time, as above. Ask only what needs the person's
   knowledge or would be expensive to get wrong; for everything else, say in one line what you will base it on.
4. **Record every answer** in the decisions log, in the folder it belongs to:
   - shared by every role (workspace setup, repo tiers, ownership, mapping depth): the workspace folder, or
     `hiring/_repo/` for one repo
   - this role only: the role folder

   `decisions.py add <folder> --stage <stage> --key <key> --value '<value>' [--by <name>] [--note <why>]`, or
   `--skipped` instead of `--value`.
5. **Changing an earlier answer** replaces it (the old value is kept in the log). Then say which outputs depend on
   it and offer to redo them. For a focus change, `focus.py stale <role folder>` lists them.

## The focus

`focus.md` in the role folder is free text from the hiring manager about what to concentrate on ("focus on the
payment library and how the two services use it; the hire will own payments"). Every stage:

- reads it after the maps, and lets it set **where to look and what to weigh**: which repos and modules to study
  first, which hard problems rank highest, what the questions probe;
- when it names a library or module, runs `trace_usage.py <workspace-or-repo> <library> --out
  <role>/usage-<library>.md` once and grounds the work in the real import and call sites;
- records the focus version it used: `Focus: <version>` in the header of Markdown outputs, `"focus_version"` in
  JSON outputs (rubric.json, interviews/core.json). In anything public (the job posting), put it in an HTML comment,
  `<!-- Focus: <version> -->`, so it never shows in the posting.

The focus describes the **work**. It can't add criteria about people (age, gender, origin, religion, family,
health, schools, appearance) and can't switch off redaction, evidence checks or the rubric: `focus.py check`
rejects that, and `check_ready.py` stops until the text is fixed. If the manager insists, explain why in one
sentence and offer the work-based version ("strong fundamentals in distributed systems" instead of "top university").

## Decisions per stage

| Stage | Skill | Decisions (at most three) | If none (skipped or unanswered) |
|---|---|---|---|
| `workspace` | hiring-workspace | which repos are in scope; which are primary (full map) or supporting (service card); where the workspace lives | can't continue without the repos; with no tiers, every repo is mapped in full; the workspace location must be given |
| `map` | map-codebase | which areas to map in depth; whether repos built from one template share one full map | every area to the same depth; each repo mapped on its own |
| `system` | hiring-workspace | who owns each repo; what unmatched internal hosts are; which cross-repo flows matter for this hire | ownership written as "unknown"; hosts listed under Gaps; every flow described equally |
| `plan` | hiring-plan | the focus text; scope across repos (share of the work per repo); role design | no focus; no scope weights; the brief lists the role designs without choosing one |
| `profile` | repo-profile | order of the hard problems; which repos and modules the profile covers | ordered by the risk the maps show; covers the whole scope at equal depth |
| `jd` | write-job-description | how much of the system to describe publicly; pay range; location | work described, internals never named; `[insert: …]` placeholders for pay and location |
| `rubric` | hiring-rubric | must-haves; criteria weights; scope weights per repo | must-haves and equal weights proposed from the profile for approval; no scope weights |
| `screen` | screen-candidates | which CVs (all or a subset); shortlist size; handling of flagged CVs | every CV in `cvs/`; no shortlist cut-off, everyone ranked; flagged CVs listed for human review, never excluded |
| `interview` | interview-kit | panel split (who asks which criteria); length; stage | no panel (one interviewer); 60 minutes; kits for every ranked candidate who meets the must-haves |
| `close` | close-round | delete the CVs; keep the report | nothing is deleted until the person answers: deletion can't be undone |
