# Planning checkpoints

Every stage starts with a short planning checkpoint, so the hiring manager steers the work where their knowledge
matters, and nothing they already answered is asked again. Each skill's own `## Planning checkpoint` section
lists the decisions for its stage; this file says how to run one.

## How to run a checkpoint

1. **Run the gate first.** `check_ready.py <repo-or-workspace> --role <role> --stage <stage>` prints what is
   already decided for this stage, and any assumptions still waiting for confirmation.
2. **Reuse what is decided.** Never re-ask a recorded decision. Name it in one line instead ("Using the scope
   weights you set on 8 Nov: payments-lib 50%, checkout-svc 30%, billing-svc 20%").
3. **Show one plan with recommended defaults.** At most three decisions, each with a recommended default and a
   one-line reason drawn from the maps, the system map, the focus or the brief:

   ```
   Plan for the rubric
   1. Scope across repos: payments-lib 50% · checkout-svc 30% · billing-svc 20%
      (the focus names the payment library; the usage trace shows checkout charges and billing refunds)
   2. Must-haves: idempotent payment flows; production Python services
      (the two hardest problems in the profile)
   3. Weight of on-call experience: 10% (supporting repo infra is owned by the platform team)
   Also assuming: anchors from the profile's examples; rubric version 1.
   Reply "approve all", or change any item ("1: 60/20/20").
   ```

   Ask only what a wrong guess would make expensive, or what needs the manager's knowledge (ownership, priorities,
   pay). Everything else is a default listed under "Also assuming".
4. **Take "approve all" or changes one at a time.** If they change one item, update the plan and show only the
   changed line. Don't open new questions unless an answer creates one.
5. **Record every answer** in the decisions log, in the folder it belongs to:
   - shared by every role (workspace setup, repo tiers, ownership, mapping depth): the workspace folder, or
     `hiring/_repo/` for one repo
   - this role only: the role folder

   `decisions.py add <folder> --stage <stage> --key <key> --value '<value>' [--by <name>] [--note <why>]`
6. **Unattended or no answer?** Take the recommended defaults, record each with `--assumed`, and start every output
   built on them with a line: *Draft: based on N assumptions not yet confirmed (see decisions.json).*
   `decisions.py pending` lists them for the manager later; `decisions.py confirm` clears them.
   Never assume past an irreversible step: approving the rubric, deleting data, sending anything to candidates.
7. **Changing an earlier answer** replaces it (the old value is kept in the log). Then say which outputs depend on
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

| Stage | Skill | Decisions (at most three) | Recommended default |
|---|---|---|---|
| `workspace` | hiring-workspace | which repos are in scope; which are primary (full map) or supporting (service card); where the workspace lives | primary: the repos the focus or brief names, or the hire will change most; others supporting; workspace outside every repo |
| `map` | map-codebase | which areas to map in depth; whether repos built from one template share one full map | areas the focus names; one full map per template group |
| `system` | hiring-workspace | who owns each repo; what unmatched internal hosts are; which cross-repo flows matter for this hire | "unknown" for owners (recorded as assumed); flows that touch primary repos |
| `plan` | hiring-plan | the focus text; scope across repos (share of the work per repo); role design | focus from the manager's words; scope from the focus and usage trace |
| `profile` | repo-profile | order of the hard problems; which repos and modules the profile covers | order by focus, then by risk in the maps |
| `jd` | write-job-description | how much of the system to describe publicly; pay range; location | describe the work, never internal names; the questions in that skill |
| `rubric` | hiring-rubric | must-haves; criteria weights; scope weights per repo | from the profile's hard problems and the plan's scope |
| `screen` | screen-candidates | which CVs (all or a subset); shortlist size; handling of flagged CVs | all CVs in `cvs/`; top 8 or a quarter, whichever is larger; flagged CVs go to human review, never silently excluded |
| `interview` | interview-kit | panel split (who asks which criteria); length; stage | one interviewer, 60 minutes, first technical interview |
| `close` | close-round | keep the report or not | always ask: deletion can't be undone |
