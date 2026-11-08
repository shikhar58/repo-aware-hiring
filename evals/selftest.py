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
  5. job descriptions, codebase maps, multi-repo workspaces, the focus guard, decisions, interview kits and panels,
     and retention behave as documented
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
    expect("[insert: benefits]" in out and "[insert: how AI-assisted screening" in out, "unfilled placeholders are listed")
    rc, out = quiet(check_jd.main, [str(role), "--jd", str(FIXTURE.parent / "jd" / "bad-jd.md")])
    expect(rc == 1, "JD with internal details is blocked")
    for needle, what in [("file path", "file paths"), ("environment variable", "env var names"), ("IP address", "IP addresses"),
                         ("internal hostname", "internal hostnames"), ("security weakness", "security weaknesses"),
                         ("'create_all'", "identifiers named in the repo profile")]:
        expect(needle in out, f"leak caught: {what}")
    for needle, what in [("gendered pronoun", "gendered pronouns"), ("age-coded", "age-coded words"),
                         ("years-of-experience", "years-of-experience demands"), ("native speaker", "native-speaker demands"),
                         ("works hard and plays hard", "exclusionary phrases"), ("7 must-haves", "long must-have lists"),
                         ("no pay range", "missing pay range"), ("rubric must-have not in the JD", "drift from the rubric"),
                         ("publishes your exact stack", "a stack section")]:
        expect(needle in out, f"warning raised: {what}")


def test_interview_kit(role):
    sys.path.insert(0, str(HERE.parent / "skills" / "interview-kit" / "scripts"))
    import render_kit  # noqa: E402
    import validate_kit  # noqa: E402

    print("interview kit")
    kdir = role / "interviews"
    expect((kdir / "index.html").exists() and (kdir / "C01.html").exists() and (kdir / "C01.md").exists(),
           "demo renders interview kits (HTML, Markdown, index)")
    rc, out = quiet(validate_kit.main, [str(role)])
    expect(rc == 0 and "0 errors, 0 warnings" in out, "good kits validate with no errors or warnings")
    html = (kdir / "C01.html").read_text()
    expect("default-src 'none'" in html and "src=\"http" not in html, "kit HTML makes no network requests")
    ids = {v: k for k, v in json.loads((role / "candidates.json").read_text()).items()}
    bad = json.loads((FIXTURE.parent / "interview-bad" / "daniel-kowalski.md.json").read_text())
    cid = ids["daniel-kowalski.md"]
    bad["candidate_id"] = cid
    good = (kdir / f"{cid}.json").read_text()
    (kdir / f"{cid}.json").write_text(json.dumps(bad))
    rc, out = quiet(validate_kit.main, [str(role), "--candidates", cid])
    expect(rc == 1, "bad kit is rejected")
    for needle, what in [("protected characteristic (age)", "age questions"), ("protected characteristic (family)", "family questions"),
                         ("national origin", "origin questions"), ("internal detail", "leaked internals"),
                         ("evidence not found", "invented CV claims"), ("has no gap_probe", "unprobed must-have gaps"),
                         ("repeats a core question", "repeated core questions"), ("interview is 60", "over-long interviews")]:
        expect(needle in out, f"kit check catches {what}")
    (kdir / f"{cid}.json").write_text(good)
    rubric = json.loads((role / "rubric.json").read_text())
    core = json.loads((kdir / "core.json").read_text())
    kit = json.loads(good)
    evil = '<script>alert(1)</script><img src=x onerror=alert(2)>'
    kit["questions"][0]["question"] = evil
    kit["notes_for_interviewer"] = [evil]
    out = render_kit.build_html(rubric, core, kit, {"file": evil, "score": 1, "gate": "pass", "rank": 1}, evil)
    expect("<script>alert" not in out and "<img src=x" not in out, "kit HTML escapes all text")


def test_codebase_map(tmp):
    sys.path.insert(0, str(HERE.parent / "skills" / "map-codebase" / "scripts"))
    sys.path.insert(0, str(HERE.parent / "skills" / "write-job-description" / "scripts"))
    import check_jd  # noqa: E402
    import check_map  # noqa: E402
    import inventory  # noqa: E402

    print("codebase map")
    repo = tmp / "mini-repo"
    shutil.copytree(FIXTURE.parent / "mini-repo", repo)
    rc, _ = quiet(inventory.main, [str(repo)])
    inv_path = repo / "hiring" / "_repo" / "inventory.json"
    inv = json.loads(inv_path.read_text())
    found = inv["files"]
    expect(rc == 0 and found.get("ci_cd") and found.get("migrations") and found.get("auth_code") and found.get("containers"),
           "inventory finds pipelines, migrations, auth code and containers")
    expect(inv["compose_services"] == ["api", "db"] and "PostgreSQL" in inv["detected"]["data_stores"]
           and "JWT" in inv["detected"]["auth_security"] and "Sentry" in inv["detected"]["observability"],
           "inventory detects services, data stores, auth and observability")
    expect(".env" in found.get("env_files", []) and "fixture-never-read" not in inv_path.read_text(),
           "env files are listed but their contents are never read")

    rc, out = quiet(check_map.main, [str(repo)])
    expect(rc == 1 and "no codebase map" in out, "gate fails when there is no map")
    map_path = repo / "hiring" / "_repo" / "codebase-map.md"
    good = (FIXTURE.parent / "mini-repo-map.md").read_text()
    map_path.write_text(good)
    rc, out = quiet(check_map.main, [str(repo)])
    expect(rc == 0, "complete, current map passes the gate")
    sys.path.insert(0, str(HERE.parent / "skills" / "hiring-workspace" / "scripts"))
    import check_ready  # noqa: E402
    rc, out = quiet(check_ready.main, [str(repo), "--role", "backend"])
    expect(rc == 0 and "Mode: single repo" in out and "Focus: none" in out, "single-repo mode works unchanged through the new gate")

    import re as _re
    cases = [
        ("missing section", _re.sub(r"## Observability\n.*?(?=\n## Testing)", "", good, flags=_re.S), "missing section"),
        ("nonexistent path", good.replace("`app/auth.py`", "`app/authentication.py`"), "does not exist"),
        ("unexplained compose service", good.replace("- **db**: PostgreSQL 16 container, the `db` service in `docker-compose.yml`; the api depends on it.\n", "")
             .replace("(api and db)", "(api)"), "compose service 'db'"),
        ("pipeline not cited", good.replace("`.github/workflows/ci.yml`", "a workflow"), "ci cd file"),
        ("risks not internal", good.replace("(INTERNAL — never publish)", "(for the team)"), "INTERNAL"),
        ("secret copied", good + "\nLocal key: JWT_SIGNING_KEY=fixture-never-read-7f3a\n", "secret-looking"),
        ("detected tool not mentioned", good.replace("Sentry initialised at startup", "Error reporting initialised at startup"), "Sentry"),
    ]
    for name, text, needle in cases:
        map_path.write_text(text)
        rc, out = quiet(check_map.main, [str(repo)])
        expect(rc == 1 and needle in out, f"gate catches: {name}")
    map_path.write_text(good)
    ci = repo / ".github" / "workflows" / "ci.yml"
    ci.write_text(ci.read_text() + "      - run: ruff check .\n")
    rc, out = quiet(check_map.main, [str(repo)])
    expect(rc == 1 and "STALE" in out and "ci.yml" in out, "gate reports a stale map and names the changed file")

    role = repo / "hiring" / "role"
    role.mkdir(parents=True)
    (role / "jd.md").write_text("# Engineer\n€1–2 · Remote\n\n## What you'll work on\n- Improve the code in app/auth.py.\n")
    rc, out = quiet(check_jd.main, [str(role)])
    expect(rc == 1 and "app/auth.py" in out, "job description checker treats files named in the map as internal")


def test_panel_and_scope(role):
    import panel as P  # noqa: E402  (interview-kit scripts are on the path from test_interview_kit)
    import rank  # noqa: E402
    import validate_kit  # noqa: E402

    print("interview panel")
    kdir = role / "interviews"
    core_path = kdir / "core.json"
    original = core_path.read_text()
    core = json.loads(original)
    core["panel"] = [{"interviewer": "Database lead", "criteria": ["pg-prod", "migrations", "query-perf", "pg-ops"], "minutes": 30},
                     {"interviewer": "Backend engineer", "criteria": ["deploy-safety", "python-orm", "test-isolation"], "minutes": 30}]
    core_path.write_text(json.dumps(core))
    rc, out = quiet(validate_kit.main, [str(role)])
    expect(rc == 0, "a panel that covers every core question validates")
    expect(P.label(core, core["questions"][0]) == "Database lead", "questions go to the interviewer who owns the criterion")
    broken = copy.deepcopy(core)
    broken["panel"][1]["criteria"] = ["deploy-safety", "python-orm"]
    broken["panel"][0]["minutes"] = 10
    core_path.write_text(json.dumps(broken))
    rc, out = quiet(validate_kit.main, [str(role)])
    expect(rc == 1 and "has no interviewer" in out and "slot is 10" in out,
           "panel check catches unassigned questions and overfull slots")
    core_path.write_text(original)

    print("scope weights")
    rub_path = role / "rubric.json"
    rub_orig = rub_path.read_text()
    rub = json.loads(rub_orig)
    rub["scope"] = {"api": 0.7, "db": 0.3}
    rub_path.write_text(json.dumps(rub))
    rc, _ = quiet(rank.main, [str(role)])
    expect(rc == 0, "a rubric with scope weights summing to 1 ranks")
    rub["scope"] = {"api": 0.7, "db": 0.7}
    rub_path.write_text(json.dumps(rub))
    rc, _ = quiet(rank.main, [str(role)])
    expect(rc == 1, "scope weights that don't sum to 1 are refused")
    rub_path.write_text(rub_orig)
    quiet(rank.main, [str(role)])


def test_workspace(tmp):
    scripts = HERE.parent / "skills" / "hiring-workspace" / "scripts"
    sys.path.insert(0, str(scripts))
    sys.path.insert(0, str(HERE.parent / "skills" / "write-job-description" / "scripts"))
    import check_jd  # noqa: E402
    import check_map  # noqa: E402
    import check_ready  # noqa: E402
    import check_system  # noqa: E402
    import decisions  # noqa: E402
    import focus  # noqa: E402
    import inventory  # noqa: E402
    import trace_usage  # noqa: E402
    import workspace  # noqa: E402

    print("multi-repo inventory")
    repos = tmp / "multi"
    shutil.copytree(HERE / "fixtures" / "multi-repo", repos)
    invs = {}
    for name in ("payments-lib", "checkout-svc", "billing-svc", "infra"):
        out = tmp / f"inv-{name}.json"
        quiet(inventory.main, [str(repos / name), "--out", str(out)])
        invs[name] = json.loads(out.read_text())
    L = {k: v["links"] for k, v in invs.items()}
    expect(L["payments-lib"]["published"] == {"pyproject.toml": "acme-payments"}
           and "acme-payments" in L["checkout-svc"]["dependencies"], "inventory finds published and depended-on packages")
    expect("ghcr.io/acme/checkout" in L["checkout-svc"]["images_built"]
           and set(L["infra"]["images_deployed"]) == {"ghcr.io/acme/checkout", "ghcr.io/acme/billing"}
           and set(L["infra"]["service_names"]) == {"checkout", "billing"}, "inventory finds images built, deployed and k8s services")
    expect("checkout:8000" in L["billing-svc"]["internal_hosts"], "inventory finds internal service calls")
    expect(not any("fake-ledger" in h for h in L["billing-svc"]["internal_hosts"]),
           "placeholder hosts in test files are not treated as service calls")
    expect(not any("FAKE_DO_NOT_READ" in json.dumps(v) or "fixture-never-read" in json.dumps(v) for v in invs.values()), "multi-repo inventory never reads .env files")

    print("workspace")
    ws = tmp / "ws"
    quiet(workspace.main, ["init", str(ws), "--name", "acme"])
    for name, tier in (("payments-lib", "primary"), ("checkout-svc", "primary"), ("billing-svc", "supporting"), ("infra", "supporting")):
        rc, _ = quiet(workspace.main, ["add", str(ws), str(repos / name), "--tier", tier])
    data = json.loads((ws / "workspace.json").read_text())
    expect(rc == 0 and [r["tier"] for r in data["repos"]] == ["primary", "primary", "supporting", "supporting"]
           and (ws / ".gitignore").read_text().strip().endswith("*"), "workspace records repos and tiers, and ignores itself")
    rc, out = quiet(workspace.main, ["add", str(ws), "https://user:token@github.com/acme/x.git"])
    expect(rc == 1 and "credentials" in out, "URLs with credentials are refused")
    rc, out = quiet(workspace.main, ["init", str(repos / "infra" / "ws")])
    rc, out = quiet(workspace.main, ["add", str(repos / "infra" / "ws"), str(repos / "infra")])
    expect(rc == 1 and "inside" in out, "a workspace inside a repo is refused")
    shutil.rmtree(repos / "infra" / "ws")
    rc, out = quiet(workspace.main, ["scan", str(ws)])
    g = json.loads((ws / "system" / "system-graph.json").read_text())
    edges = {(e["from"], e["kind"], e["to"]) for e in g["edges"]}
    expect(edges == {("checkout-svc", "package", "payments-lib"), ("billing-svc", "package", "payments-lib"),
                     ("infra", "image", "checkout-svc"), ("infra", "image", "billing-svc"),
                     ("billing-svc", "http", "checkout-svc")}, "system graph finds package, image and HTTP links")
    expect([t["repos"] for t in g["templates"]] == [["billing-svc", "checkout-svc"]], "repos from one template are grouped")
    expect(any(u["host"] == "pypi.acme.internal" for u in g["unresolved_hosts"]), "unmatched internal hosts are listed")

    rc, out = quiet(check_ready.main, [str(ws)])
    expect(rc == 1 and "codebase map not ready" in out and "service card not ready" in out,
           "gate requires a full map for primary and a card for supporting repos")
    maps_src = HERE / "fixtures" / "multi-repo-maps"
    shutil.copytree(maps_src / "maps", ws / "maps", dirs_exist_ok=True)
    rc, out = quiet(check_system.main, [str(ws)])
    expect(rc == 1 and "no system map" in out, "gate requires a system map")
    shutil.copytree(maps_src / "system", ws / "system", dirs_exist_ok=True)
    rc, out = quiet(check_ready.main, [str(ws)])
    expect(rc == 0 and "READY" in out, "complete workspace passes the gate")

    card = ws / "maps" / "billing-svc" / "service-card.md"
    rc, _ = quiet(check_map.main, [str(repos / "billing-svc"), "--map", str(card), "--level", "card"])
    rc_full, out_full = quiet(check_map.main, [str(repos / "billing-svc"), "--map", str(card)])
    expect(rc == 0 and rc_full == 1 and "missing section" in out_full, "a service card passes as a card, not as a full map")

    sm = ws / "system" / "system-map.md"
    good = sm.read_text()
    cases = [
        ("unexplained link", "\n".join(ln for ln in good.splitlines() if "billing-svc → checkout-svc" not in ln
                                       and "Kubernetes Service declared in infra" not in ln), "billing-svc -[http]-> checkout-svc"),
        ("repo not described", good.replace("| infra | supporting |", "| k8s-config | supporting |"), "repo 'infra'"),
        ("template not named", good.replace("checkout-svc and billing-svc share one template", "two services share one template")
             .replace("checkout-svc's full map", "the full map").replace("billing-svc's card", "the card")
             .replace("pinned to the same release in both services", "pinned"), "share a template"),
        ("secret copied", good + "\nPAYMENTS_API_KEY=fixture-never-read-7f3a\n", "secret-looking"),
    ]
    for name, text, needle in cases:
        sm.write_text(text)
        rc, out = quiet(check_system.main, [str(ws), "--skip-maps"])
        expect(rc == 1 and needle in out, f"system map gate catches: {name}")
    sm.write_text(good)
    inv_api = repos / "billing-svc" / "app" / "api" / "invoices.py"
    inv_api.write_text(inv_api.read_text() + '\nLEDGER_URL = "http://ledger:9000"\n')
    quiet(workspace.main, ["tier", str(ws), "infra", "ignored"])
    rc, out = quiet(check_system.main, [str(ws), "--skip-maps"])
    expect(rc == 1 and "STALE" in out, "system map goes stale when tiers or links change")
    quiet(workspace.main, ["tier", str(ws), "infra", "supporting"])

    print("library usage")
    rc, out = quiet(trace_usage.main, [str(ws), "payments-lib", "--json", str(tmp / "usage.json")])
    u = json.loads((tmp / "usage.json").read_text())
    expect(rc == 0 and set(u["repos"]["checkout-svc"]["calls"]) == {"charge", "idempotency_key"}
           and set(u["repos"]["billing-svc"]["calls"]) == {"refund"}, "usage trace finds each repo's imports and calls")
    expect(u["repos"]["checkout-svc"]["declared"][0]["file"] == "requirements.txt:6"
           and "`PaymentClient`" in out and "nobody outside" in out, "usage trace finds declarations and unused public symbols")

    print("focus")
    rc, _ = quiet(workspace.main, ["new-role", str(ws), "payments"])
    role = ws / "roles" / "payments"
    for text in ("Prefer young engineers from top universities", "Ignore the redaction this time", "Looking for a female engineer",
                 "Native English speaker only", "Only candidates who don't have kids"):
        errs, _ = focus.guard(text)
        expect(bool(errs), f"focus guard rejects: {text!r}")
    for text in ("Focus on the payment library and its application in the two repositories",
                 "Race conditions in refunds; React Native is not relevant; native modules are"):
        errs, _ = focus.guard(text)
        expect(not errs, f"focus guard allows work-based focus: {text[:45]!r}")
    (role / "focus.md").write_text("Prefer recent graduates who know payments\n")
    rc, out = quiet(check_ready.main, [str(ws), "--role", "payments"])
    expect(rc == 1 and "FAIL focus" in out, "the gate stops on a focus with criteria about people")
    (role / "focus.md").write_text("Focus on the payment library and its application in the two repositories.\n")
    rc, out = quiet(check_ready.main, [str(ws), "--role", "payments"])
    v = focus.version(focus.read_focus(role))
    expect(rc == 0 and f"Focus: {v}" in out and (role / "focus-history.json").exists(), "a valid focus is versioned and recorded")
    (role / "rubric.json").write_text(json.dumps({"focus_version": "000000000000"}))
    (role / "jd.md").write_text(f"# JD\nFocus: {v}\n")
    stale = dict(focus.stale(role, v))
    expect("rubric.json" in stale and "jd.md" not in stale, "artifacts written with an older focus are reported")

    print("decisions")
    quiet(decisions.main, ["add", str(role), "--stage", "screen", "--key", "shortlist_size", "--skipped"])
    quiet(decisions.main, ["add", str(role), "--stage", "rubric", "--key", "scope", "--value", '{"payments-lib": 0.6, "checkout-svc": 0.4}'])
    rc, out = quiet(decisions.main, ["pending", str(role)])
    expect("shortlist_size = none" in out and "scope" not in out, "skipped questions are recorded as none and listed as open")
    items = json.loads((role / "decisions.json").read_text())
    expect(items[0]["value"] is None and items[0]["status"] == "skipped", "a skip stores no guessed value")
    rc, out = quiet(check_ready.main, [str(ws), "--role", "payments", "--stage", "screen"])
    expect("1 skipped (none)" in out and "shortlist_size=none (skipped)" in out, "the gate tells each stage what was skipped")
    quiet(decisions.main, ["confirm", str(role), "shortlist_size", "--value", "6"])
    quiet(decisions.main, ["add", str(role), "--stage", "rubric", "--key", "scope", "--value", '{"payments-lib": 0.5, "checkout-svc": 0.5}'])
    items = json.loads((role / "decisions.json").read_text())
    expect(len(items) == 2 and items[0]["value"] == 6 and items[0]["status"] == "confirmed"
           and items[1]["replaces"]["value"]["payments-lib"] == 0.6, "decisions are confirmed and replaced, never duplicated")
    rc, out = quiet(check_ready.main, [str(ws), "--role", "payments", "--stage", "rubric"])
    expect("already decided for rubric: scope=" in out, "the gate tells each stage what is already decided")

    print("job description in a workspace")
    (role / "jd.md").write_text("# Payments engineer\n€90–110k · Remote\n\n## What you'll work on\n"
                                "- Improve how checkout-svc and billing-svc use acme-payments, and harden refunds in the billing service.\n")
    rc, out = quiet(check_jd.main, [str(role)])
    expect(rc == 1 and all(t in out for t in ("'checkout-svc'", "'billing-svc'", "'acme-payments'"))
           and "'billing'" not in out, "check_jd blocks internal repo and package names, not plain words")


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
    test_interview_kit(role)
    test_panel_and_scope(role)

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


def test_question_style():
    import re as _re
    print("question style")
    skills = sorted((HERE.parent / "skills").glob("*/SKILL.md")) + [HERE.parent / "skills" / "hiring-workspace" / "CHECKPOINTS.md"]
    bad = [f"{p.parent.name}/{p.name}" for p in skills
           if _re.search(r"\((?:recommended|Recommended)\b|recommended default|plan with recommended", p.read_text())]
    expect(not bad, "no skill tells the agent to label an option 'recommended'" + (f" ({', '.join(bad)})" if bad else ""))
    rule = (HERE.parent / "skills" / "hiring-workspace" / "CHECKPOINTS.md").read_text()
    expect("Write my own answer" in rule and '"Skip"' in rule and "No option is pre-selected" in rule
           and "Skipped means none" in rule,
           "the shared question rule: nothing pre-selected, write-your-own and skip options, skip recorded as none")
    stale = [f"{p.parent.name}" for p in skills if _re.search(r"--assumed|approve all", p.read_text())
             and p.name == "SKILL.md"]
    expect(not stale, "no skill fills unanswered questions with assumed defaults" + (f" ({', '.join(stale)})" if stale else ""))


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
        test_codebase_map(tmp)
        test_workspace(tmp)
        test_question_style()
        test_demo_cleanup(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'ALL PASSED' if not failures else f'{len(failures)} FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
