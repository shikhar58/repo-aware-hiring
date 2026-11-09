# Privacy

repo-aware-hiring is an open-source plugin that runs inside your own coding agent. It has no server, no account and
no telemetry, and its author receives no data from you or your candidates.

## What the plugin itself does

- **Reads** the repositories you point it at, and the CVs you place in a role folder.
- **Writes** maps, rubrics, scores, reports and interview kits to a git-ignored `hiring/` folder in your repository,
  or to a private workspace folder you choose. It never writes into your repositories' code.
- **Never reads** environment files (`.env` and similar), and blocks secrets from being copied into its maps.
- **Makes no network requests.** The only programs it runs are `git` (to read commit ids, and to clone or pull a
  repository you add to a workspace by URL, using your own git credentials) and `pdftotext` (to read PDF CVs,
  locally). The HTML reports and interview kits it produces make no network requests either.

## What your agent sends to its model provider

Like any other task, your agent sends the code it reads and the text it works on to the model provider it is
configured with, under the agreements you already have with that provider. For screening, CVs are redacted (names,
contact details, age, nationality and similar details removed) before the model scores them. Check that your
agreements allow candidate data to be processed this way.

## Candidate data

You are the controller of your candidates' data. The plugin helps you meet your obligations:

- **Retention:** `close-round` deletes candidate data when a role closes and keeps only a pseudonymous audit record;
  `cleanup.py sweep` lists rounds past your retention period.
- **Erasure:** remove a candidate's files and re-rank (see the `close-round` skill).
- **Notice:** candidates must be told that AI helps screen them; see [docs/COMPLIANCE.md](docs/COMPLIANCE.md).

## Contact

Questions about this policy: open an issue at https://github.com/shikhar58/repo-aware-hiring/issues. Please don't
include candidate data or code from your repositories. Security issues: see [SECURITY.md](SECURITY.md).
