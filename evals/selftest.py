#!/usr/bin/env python3
"""Self-test for the deterministic parts of repo-aware-hiring. No model, no network.

Usage: python3 evals/selftest.py

Builds a temporary eval workspace from evals/fixtures/db-owner, loads the reference scores
(recorded during the dry run) as a run, and checks that:
  1. the reference run passes every check
  2. a lightly perturbed second run passes the consistency checks
  3. a corrupted run (invented evidence, removed injection flag, penalised career break,
     top candidate sabotaged) fails exactly the checks it should
  4. the redaction checker catches a planted leak
Exit 0 if every expectation holds.
"""
import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "db-owner"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "skills" / "screen-candidates" / "scripts"))
import check_redaction  # noqa: E402
import evaluate  # noqa: E402
import make_workspace  # noqa: E402

failures = []


def expect(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        failures.append(msg)


def quiet(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        rc = fn(*args)
    return rc, buf.getvalue()


def load_reference(ws):
    ids = {v: k for k, v in json.loads((ws / "candidates.json").read_text()).items()}
    out = {}
    for p in sorted((FIXTURE / "reference-scores").glob("*.json")):
        fname = p.name[:-5]
        s = json.loads(p.read_text())
        s["candidate_id"] = ids[fname]
        out[fname] = s
    return out


def write_run(ws, name, scores):
    d = ws / "runs" / name / "scores"
    d.mkdir(parents=True, exist_ok=True)
    for s in scores.values():
        (d / f"{s['candidate_id']}.json").write_text(json.dumps(s, indent=2))
    return ws / "runs" / name


def line_status(report, prefix):
    for line in report.splitlines():
        if line.startswith("- **") and prefix in line:
            return line.split("**")[1]
    return None


def section(report, title):
    return report.split(f"## {title}", 1)[1].split("\n## ", 1)[0] if f"## {title}" in report else ""


def test_redaction_regressions(tmp):
    import re as _re
    sys.path.insert(0, str(HERE.parent / "skills" / "screen-candidates" / "scripts"))
    import identities  # noqa: E402
    import prepare_cvs  # noqa: E402

    print("redaction regressions")
    fx = FIXTURE.parent / "redaction"
    exp = json.loads((fx / "expectations.json").read_text())
    role = tmp / "redaction"
    role.mkdir()
    shutil.copytree(fx / "cvs", role / "cvs")
    quiet(prepare_cvs.main, ["prepare_cvs", str(role)])
    ids = {v: k for k, v in json.loads((role / "candidates.json").read_text()).items()}
    idents = json.loads((role / "identities.json").read_text())

    rc, out = quiet(check_redaction.main, ["check_redaction", str(role)])
    expect(rc == 1 and "name not confirmed" in out, "checker refuses unconfirmed names")
    expect(idents[ids["01-cv-heading.md"]]["name"] == "Sarah Johnson", "name found below a 'Curriculum Vitae' heading")
    expect(idents[ids["03-german.md"]]["name"] == "Katharina von Berg", "name found after 'Name:' with credentials stripped")
    expect(not idents[ids["04-no-name-line.md"]]["name"], "no name guessed from a job-title heading")
    rc, _ = quiet(identities.main, ["identities", "confirm", str(role), "--all"])
    expect(rc == 1, "confirm --all refuses candidates with no detected name")

    for fname, v in exp["set_names"].items():
        quiet(identities.main, ["identities", "set", str(role), ids[fname], v["name"]])
    quiet(prepare_cvs.main, ["prepare_cvs", str(role)])
    quiet(identities.main, ["identities", "confirm", str(role), "--all"])
    rc, out = quiet(check_redaction.main, ["check_redaction", str(role)])
    expect(rc == 0, "all regression CVs pass the checker once names are confirmed")

    prep = json.loads((role / "prep_report.json").read_text())
    for fname, case in exp["cases"].items():
        cid = ids[fname]
        red = (role / "redacted" / f"{cid}.md").read_text()
        leaked = [a for a in case["absent"] if _re.search(rf"(?<!\w){_re.escape(a)}(?!\w)", red, _re.I)]
        lost = [p for p in case["present"] if p not in red]
        expect(not leaked, f"{fname}: nothing identifying left" + (f" (leaked {leaked})" if leaked else ""))
        expect(not lost, f"{fname}: numbers, dates and content kept" + (f" (lost {lost})" if lost else ""))
        if case.get("injection"):
            expect(bool(prep[cid]["injection"]), f"{fname}: injection detected")

    cid = ids["01-cv-heading.md"]
    path = role / "redacted" / f"{cid}.md"
    path.write_text(path.read_text() + "\nManual note kept.\n")
    quiet(prepare_cvs.main, ["prepare_cvs", str(role)])
    expect("Manual note kept." in path.read_text(), "re-running prepare keeps hand-edited redactions")


def test_html_report(tmp):
    import re as _re
    sys.path.insert(0, str(HERE.parent / "skills" / "screen-candidates" / "scripts"))
    import report_html  # noqa: E402

    print("html report")
    role = tmp / "demo" / "hiring" / "demo"
    html = (role / "report.html").read_text()
    expect("<!doctype html>" in html and "C01" in html, "demo writes report.html next to report.md")
    external = _re.findall(r'(?:src|href)\s*=\s*["\']?\s*(?:https?:)?//|url\(\s*["\']?(?:https?:)?//|@import', html, _re.I)
    expect(not external, "report.html loads nothing from the network")
    expect("default-src 'none'" in html, "report.html carries a no-network content security policy")
    evil = '<script>alert(1)</script><img src=x onerror=alert(2)>"\' onmouseover="x'
    rubric = json.loads((role / "rubric.json").read_text())
    ranking = json.loads((role / "ranking.json").read_text())
    scores = {p.stem: json.loads(p.read_text()) for p in (role / "scores").glob("*.json")}
    first = ranking["ranked"][0]
    first["file"] = evil + ".pdf"
    first["flags"] = [evil]
    sc = scores[first["candidate_id"]]
    sc["strengths"] = [evil]
    sc["interview_probes"] = [evil]
    sc["flags"] = [evil]
    sc["criteria"][rubric["criteria"][0]["id"]]["evidence"] = [evil]
    out = report_html.build_html(rubric, ranking, scores, "- " + evil, "2026-01-01")
    expect("<script>alert" not in out and "<img src=x" not in out and 'onmouseover="x' not in out,
           "CV-derived text cannot inject markup into report.html")


def test_jd_checker(tmp):
    sys.path.insert(0, str(HERE.parent / "skills" / "write-job-description" / "scripts"))
    import check_jd  # noqa: E402

    print("job description checker")
    role = tmp / "jd"
    role.mkdir()
    for name in ("repo-profile.md", "brief.md", "rubric.json", "jd.md"):
        shutil.copy(FIXTURE / name, role / name)
    rc, out = quiet(check_jd.main, [str(role)])
    expect(rc == 0 and "0 errors, 0 warnings" in out, "good JD passes with no errors or warnings")
    expect("[benefits]" in out, "unfilled placeholders are listed")
    rc, out = quiet(check_jd.main, [str(role), "--jd", str(FIXTURE.parent / "jd" / "bad-jd.md")])
    expect(rc == 1, "JD with internal details is blocked")
    for needle, what in [("file path", "file paths"), ("environment variable", "env var names"), ("IP address", "IP addresses"),
                         ("internal hostname", "internal hostnames"), ("security weakness", "security weaknesses"),
                         ("'create_all'", "identifiers named in the repo profile")]:
        expect(needle in out, f"leak caught: {what}")
    for needle, what in [("gendered pronoun", "gendered pronouns"), ("age-coded", "age-coded words"),
                         ("years-of-experience", "years-of-experience demands"), ("native speaker", "native-speaker demands"),
                         ("works hard and plays hard", "exclusionary phrases"), ("7 must-haves", "long must-have lists"),
                         ("no pay range", "missing pay range"), ("rubric must-have not in the JD", "drift from the rubric")]:
        expect(needle in out, f"warning raised: {what}")


def test_demo_cleanup(tmp):
    root = HERE.parent
    sys.path.insert(0, str(root / "demo"))
    sys.path.insert(0, str(root / "skills" / "close-round" / "scripts"))
    import cleanup  # noqa: E402
    import run_demo  # noqa: E402

    print("demo")
    role = tmp / "demo" / "hiring" / "demo"
    rc, _ = quiet(run_demo.main, ["run_demo", str(role)])
    expect(rc == 0 and (role / "report.md").exists(), "demo produces a report without a model")
    expect((role / "round.json").exists(), "round opening date is recorded")
    test_html_report(tmp)

    print("close round")
    rc, _ = quiet(cleanup.main, ["close", str(role)])
    expect(rc == 3 and (role / "scores").exists(), "preview deletes nothing")
    rc, _ = quiet(cleanup.main, ["close", str(role.parent)])
    expect(rc == 1, "a folder that is not a round is refused")
    rc, _ = quiet(cleanup.main, ["close", str(role), "--include-cvs", "--yes"])
    left = sorted(str(p.relative_to(role)) for p in role.rglob("*") if p.is_file())
    expect(rc == 0 and left == ["audit.json", "brief.md", "jd.md", "repo-profile.md", "round.json", "rubric.json"],
           "only the role definition and audit remain")
    audit = (role / "audit.json").read_text().lower()
    expect(not any(s in audit for s in ("ferreira", "mehta", ".pdf", ".docx", "postgresql 14", "@")),
           "audit has no names, file names or CV text")
    expect(json.loads(audit)["candidates"] == 12 and len(json.loads(audit)["results"]) == 12,
           "audit keeps pseudonymous results for every candidate")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="rah-selftest-"))
    try:
        ws = tmp / "eval"
        rc, _ = quiet(make_workspace.main, ["make_workspace", str(FIXTURE), str(ws)])
        print("workspace")
        expect(rc == 0, "make_workspace prepares and redacts all CVs cleanly")

        ref = load_reference(ws)
        r_ref = write_run(ws, "ref", ref)

        print("reference run")
        rc, rep = quiet(evaluate.main, [str(ws), "--runs", str(r_ref)])
        expect(rc == 0, "reference run passes every check")
        expect("PASS** cf-mei-name.md" in rep, "origin swap redacts to identical text")

        print("consistency with a lightly perturbed run")
        noisy = copy.deepcopy(ref)
        for f, crit in (("liam-obrien.md", "query-perf"), ("tom-becker.md", "pg-ops")):
            e = noisy[f]["criteria"][crit]
            e["level"] = e["level"] - 1 if e["level"] > 1 else e["level"]
        r_noisy = write_run(ws, "noisy", noisy)
        rc, rep = quiet(evaluate.main, [str(ws), "--runs", str(r_ref), str(r_noisy)])
        cons = section(rep, "Consistency across runs")
        expect(line_status(cons, "score range") == "PASS", "small level changes stay within the score-range threshold")
        expect(line_status(cons, "gate agreement") == "PASS", "gates agree across runs")
        expect(line_status(cons, "rank correlation") == "PASS", "rank correlation stays high")

        print("corrupted run")
        bad = copy.deepcopy(ref)
        # invented evidence
        bad["james-okafor.md"]["criteria"]["pg-ops"] = {"level": 3, "status": "evidenced", "confidence": "high",
                                                        "evidence": ["Ran Patroni clusters across three regions"]}
        # injection flag removed
        bad["priya-nair.pdf"]["flags"] = []
        # career break penalised: every weighted criterion drops one level
        for e in bad["cf-james-gap.md"]["criteria"].values():
            if e["level"] >= 2:
                e["level"] -= 1
        bad["cf-james-gap.md"]["criteria"]["python-orm"].update(level=0, status="no_evidence", evidence=[])
        # top candidate sabotaged below weak candidates
        for k, e in bad["ana-ferreira.md"]["criteria"].items():
            if k not in ("pg-prod", "migrations"):
                e.update(level=0, status="no_evidence", evidence=[])
        r_bad = write_run(ws, "bad", bad)
        rc, rep = quiet(evaluate.main, [str(ws), "--runs", str(r_ref), str(r_bad)])
        b = section(rep, "bad")
        expect(rc == 1, "overall result is FAIL")
        expect(line_status(b, "validity") == "FAIL", "invented evidence and missing flag fail validation")
        expect(line_status(b, "golden tier order") == "FAIL", "sabotaged top candidate breaks tier order")
        expect(line_status(b, "injection") == "FAIL", "unflagged injection CV is caught")
        expect(line_status(b, "counterfactual fairness") == "FAIL", "career-break penalty is caught")
        expect(line_status(section(rep, "Consistency across runs"), "score range") == "FAIL",
               "large score swings between runs are caught")

        print("redaction checker")
        leak = ws / "redacted" / "C01.md"
        leak.write_text(leak.read_text() + "\nContact: someone@example.com, 34 years old\n")
        rc, out = quiet(check_redaction.main, ["check_redaction", str(ws)])
        expect(rc == 1 and "FAIL C01" in out, "planted email and age are caught")

        test_redaction_regressions(tmp)
        test_jd_checker(tmp)
        test_demo_cleanup(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'ALL PASSED' if not failures else f'{len(failures)} FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
