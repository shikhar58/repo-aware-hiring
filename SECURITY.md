# Security policy

This project processes CVs, which contain personal data, and passes their text to a language model.
The issues that matter most are therefore:

- **Redaction bypasses:** a name, contact detail, date of birth, nationality or similar that reaches
  `redacted/` and passes `check_redaction.py`.
- **Prompt injection that changes a score:** text in a CV that raises a candidate's score or ranking
  without being flagged.
- **Evidence validation bypasses:** a score that passes `validate_scores.py` with evidence not in the CV.
- **Data left behind:** personal data that survives `close-round`.
- **Unsafe file handling:** anything that lets a crafted CV file read or write outside the role folder
  or run code.

## Reporting

Please report these privately using GitHub's **Report a vulnerability** button (Security tab →
Advisories), not in a public issue. Include a minimal synthetic CV that reproduces the problem.
**Never send real candidate data.**

You can expect an acknowledgement within 7 days. Confirmed bypasses get a fix, a regression case in
`evals/fixtures/redaction/` and credit in the changelog unless you prefer otherwise.

## Supported versions

Only the latest release receives fixes while the project is pre-1.0.

## Scope notes

Redaction patterns cover English, French, German, Spanish, Italian, Dutch and Portuguese field labels.
CVs in other languages rely on the agent's manual review, which this project documents but cannot
guarantee. Reports that improve coverage for other languages are welcome as normal issues or pull requests.
