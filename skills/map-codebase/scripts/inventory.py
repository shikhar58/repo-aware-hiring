#!/usr/bin/env python3
"""Deterministic inventory of a codebase: the checklist the agent must explain in codebase-map.md.

Usage: python3 inventory.py <repo_dir> [--out hiring/_repo/inventory.json]

Finds, without a model and without reading secret values:
  languages (by lines of code), manifests and dependencies, services and packages, containers,
  CI/CD pipelines, deployment and infrastructure-as-code, database migrations and schema, API specs,
  data stores and queues, authentication and security tooling, observability, tests, and env files
  (existence only: their contents are never read).
Also records a fingerprint of the structurally important files, so check_map.py can tell when the
map is out of date, and the git commit when available. Standard library only.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist", "build", "target", "vendor",
             ".next", ".nuxt", ".cache", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "coverage",
             ".idea", ".vscode", "hiring", ".terraform", "site-packages", "bower_components", ".gradle", "out"}
MAX_FILES = 60000
MAX_READ = 400_000  # bytes read per file for detection

LANG = {".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TypeScript", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".scala": "Scala",
        ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".cpp": "C++", ".cc": "C++", ".c": "C", ".h": "C/C++ header",
        ".swift": "Swift", ".m": "Objective-C", ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir", ".sql": "SQL",
        ".sh": "Shell", ".vue": "Vue", ".svelte": "Svelte", ".tf": "Terraform", ".hcl": "HCL", ".proto": "Protobuf",
        ".graphql": "GraphQL", ".css": "CSS", ".scss": "CSS", ".html": "HTML", ".yaml": "YAML", ".yml": "YAML"}
SOURCE_LANGS = {"Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "Kotlin", "Scala", "Ruby", "PHP", "C#",
                "C++", "C", "Swift", "Objective-C", "Dart", "Elixir", "Vue", "Svelte"}

MANIFESTS = re.compile(r"^(package\.json|pyproject\.toml|requirements[\w.-]*\.txt|Pipfile|setup\.py|setup\.cfg|go\.mod|"
                       r"Cargo\.toml|pom\.xml|build\.gradle(\.kts)?|settings\.gradle(\.kts)?|Gemfile|composer\.json|"
                       r"[\w.-]+\.csproj|mix\.exs|pubspec\.yaml|deno\.json)$")
CONTAINERS = re.compile(r"^(Dockerfile[\w.-]*|[\w.-]*\.Dockerfile|(docker-)?compose[\w.-]*\.ya?ml|\.dockerignore)$")
CI_PATHS = re.compile(r"(^|/)(\.github/workflows/[^/]+\.ya?ml|\.gitlab-ci\.yml|Jenkinsfile|\.circleci/config\.ya?ml|"
                      r"azure-pipelines\.ya?ml|bitbucket-pipelines\.yml|\.drone\.ya?ml|\.buildkite/[^/]+|"
                      r"\.travis\.yml|cloudbuild\.ya?ml|buildspec\.ya?ml|\.github/dependabot\.ya?ml|renovate\.json)$")
DEPLOY_PATHS = re.compile(r"(\.tf$|^Chart\.yaml$|/Chart\.yaml$|kustomization\.ya?ml$|serverless\.ya?ml$|(^|/)Procfile$|"
                          r"fly\.toml$|(^|/)app\.ya?ml$|vercel\.json$|netlify\.toml$|cdk\.json$|Pulumi\.ya?ml$|"
                          r"skaffold\.ya?ml$|(^|/)\.platform\.app\.yaml$|render\.ya?ml$|railway\.json$|ansible\.cfg$|"
                          r"(^|/)playbooks?/[^/]+\.ya?ml$|copilot/.*manifest\.yml$)")
K8S_KIND = re.compile(r"^kind:\s*(Deployment|StatefulSet|DaemonSet|Service|Ingress|CronJob|Job|ConfigMap|HorizontalPodAutoscaler)\s*$", re.M)
MIGRATION_DIR = re.compile(r"(^|/)(migrations?|alembic|db/migrate|flyway|liquibase|prisma/migrations|schema_migrations)(/|$)", re.I)
SCHEMA_FILES = re.compile(r"(^|/)(schema\.prisma|schema\.rb|structure\.sql|schema\.sql|models\.py|ormconfig\.\w+|"
                          r"alembic\.ini|knexfile\.\w+|drizzle\.config\.\w+|sqlc\.ya?ml)$")
API_SPECS = re.compile(r"(^|/)(openapi[\w.-]*\.(ya?ml|json)|swagger[\w.-]*\.(ya?ml|json)|[\w.-]+\.proto|"
                       r"schema\.graphql|[\w.-]+\.graphqls?|asyncapi[\w.-]*\.ya?ml)$", re.I)
ENV_FILES = re.compile(r"(^|/)\.env(\.[\w-]+)?$|(^|/)[\w-]+\.env$")
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs|e2e|integration)(/|$)|(_test\.go|\.test\.[jt]sx?|\.spec\.[jt]sx?|"
                       r"(^|/)test_[\w]+\.py|_test\.py|Test\.java|_spec\.rb)$")
SECURITY_FILES = re.compile(r"(^|/)(SECURITY\.md|CODEOWNERS|\.pre-commit-config\.yaml|\.gitleaks\.toml|\.trivyignore|"
                            r"\.snyk|bandit\.ya?ml|\.bandit|\.semgrep\.ya?ml|semgrep\.ya?ml|\.github/codeql[^/]*|"
                            r"codeql[\w.-]*\.ya?ml)$")

# term -> category; matched against dependency names, compose images and source text (word boundaries)
SIGNALS = {
    "data_stores": {"postgres": "PostgreSQL", "psycopg": "PostgreSQL", "asyncpg": "PostgreSQL", "pgx": "PostgreSQL",
                    "mysql": "MySQL", "mariadb": "MariaDB", "sqlite": "SQLite", "mongo": "MongoDB", "mongoose": "MongoDB",
                    "redis": "Redis", "memcache": "Memcached", "elasticsearch": "Elasticsearch", "opensearch": "OpenSearch",
                    "dynamodb": "DynamoDB", "cassandra": "Cassandra", "clickhouse": "ClickHouse", "snowflake": "Snowflake",
                    "bigquery": "BigQuery", "neo4j": "Neo4j", "s3": "S3 / object storage", "minio": "S3 / object storage",
                    "pinecone": "Pinecone", "qdrant": "Qdrant", "pgvector": "pgvector", "weaviate": "Weaviate"},
    "queues": {"kafka": "Kafka", "rabbitmq": "RabbitMQ", "amqp": "AMQP", "celery": "Celery", "rq": "RQ", "sqs": "SQS",
               "pubsub": "Pub/Sub", "nats": "NATS", "bullmq": "BullMQ", "sidekiq": "Sidekiq", "temporal": "Temporal"},
    "orm": {"sqlalchemy": "SQLAlchemy", "sqlmodel": "SQLModel", "django": "Django ORM", "prisma": "Prisma",
            "typeorm": "TypeORM", "sequelize": "Sequelize", "drizzle": "Drizzle", "gorm": "GORM", "sqlc": "sqlc",
            "hibernate": "Hibernate", "activerecord": "ActiveRecord", "diesel": "Diesel", "ecto": "Ecto"},
    "auth_security": {"jwt": "JWT", "pyjwt": "JWT", "jsonwebtoken": "JWT", "oauth": "OAuth", "oauthlib": "OAuth",
                      "authlib": "OAuth/OIDC", "oidc": "OIDC", "saml": "SAML", "passlib": "password hashing",
                      "bcrypt": "password hashing", "argon2": "password hashing", "pwdlib": "password hashing",
                      "keycloak": "Keycloak", "auth0": "Auth0", "cognito": "Cognito", "next-auth": "NextAuth",
                      "passport": "Passport", "spring-security": "Spring Security", "devise": "Devise",
                      "casbin": "Casbin", "cors": "CORS config", "csrf": "CSRF protection", "helmet": "Helmet",
                      "vault": "secrets manager", "secretsmanager": "secrets manager", "kms": "KMS",
                      "ratelimit": "rate limiting", "slowapi": "rate limiting"},
    "observability": {"sentry": "Sentry", "prometheus": "Prometheus", "opentelemetry": "OpenTelemetry",
                      "datadog": "Datadog", "newrelic": "New Relic", "grafana": "Grafana", "jaeger": "Jaeger",
                      "structlog": "structured logging", "loguru": "logging", "winston": "logging", "pino": "logging",
                      "logfire": "Logfire", "honeycomb": "Honeycomb", "elastic-apm": "Elastic APM"},
    "proxies_gateways": {"traefik": "Traefik", "nginx": "Nginx", "caddy": "Caddy", "envoy": "Envoy",
                         "haproxy": "HAProxy", "kong": "Kong", "istio": "Istio", "cloudflare": "Cloudflare"},
    "frameworks": {"fastapi": "FastAPI", "flask": "Flask", "django": "Django", "starlette": "Starlette",
                   "express": "Express", "nestjs": "NestJS", "next": "Next.js", "react": "React", "vue": "Vue",
                   "svelte": "Svelte", "angular": "Angular", "spring-boot": "Spring Boot", "rails": "Rails",
                   "gin": "Gin", "echo": "Echo", "fiber": "Fiber", "actix": "Actix", "axum": "Axum", "laravel": "Laravel",
                   "phoenix": "Phoenix", "langgraph": "LangGraph", "langchain": "LangChain", "pydantic": "Pydantic"},
    "test_frameworks": {"pytest": "pytest", "unittest": "unittest", "jest": "Jest", "vitest": "Vitest",
                        "playwright": "Playwright", "cypress": "Cypress", "mocha": "Mocha", "junit": "JUnit",
                        "rspec": "RSpec", "testcontainers": "Testcontainers", "hypothesis": "Hypothesis"},
}


def walk(root):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info"))
        for f in sorted(filenames):
            p = Path(dirpath) / f
            if p.is_symlink():
                continue
            count += 1
            if count > MAX_FILES:
                return
            yield p


def read(p, limit=MAX_READ):
    try:
        with p.open("rb") as fh:
            return fh.read(limit).decode("utf-8", errors="replace")
    except OSError:
        return ""


def git_head(root):
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def deps_from_manifest(p, text):
    names = set()
    n = p.name
    if n == "package.json":
        try:
            d = json.loads(text)
            for k in ("dependencies", "devDependencies", "peerDependencies"):
                names |= set((d.get(k) or {}).keys())
        except ValueError:
            pass
    elif n.startswith("requirements") or n == "Pipfile":
        names |= {re.split(r"[<>=~!\[; ]", ln.strip())[0].lower() for ln in text.splitlines()
                  if ln.strip() and not ln.strip().startswith(("#", "-"))}
    else:  # pyproject, go.mod, Cargo, pom, gradle, Gemfile, composer...
        names |= {m.lower() for m in re.findall(r"[\"']([A-Za-z0-9_.\-/@]+)(?:[\[<>=~!^ ,\"'])", text)}
        names |= {m.lower() for m in re.findall(r"^\s*([A-Za-z0-9_.\-/]+)\s*=", text, re.M)}
        names |= {m.lower() for m in re.findall(r"<artifactId>([^<]+)</artifactId>", text)}
        names |= {m.lower().rsplit("/", 1)[-1] for m in re.findall(r"^\s*(?:require\s+)?([\w.\-]+/[\w.\-/]+)\s+v\d", text, re.M)}
        names |= {m.lower() for m in re.findall(r"gem\s+[\"']([\w\-]+)", text)}
    return {x for x in names if x and len(x) < 80}


def match_signals(tokens_text):
    found = defaultdict(set)
    low = tokens_text.lower()
    for cat, table in SIGNALS.items():
        for term, label in table.items():
            if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", low):
                found[cat].add(label)
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--out", default=None, help="default: <repo>/hiring/_repo/inventory.json")
    args = ap.parse_args(argv)
    root = Path(args.repo).resolve()
    out_path = Path(args.out) if args.out else root / "hiring" / "_repo" / "inventory.json"

    loc = Counter()
    files_by_lang = Counter()
    cats = defaultdict(list)
    deps = defaultdict(set)
    compose_services, compose_images = [], set()
    test_files = 0
    source_files = 0
    key_hash = hashlib.sha256()
    key_files = {}
    dep_text = []
    top_dirs = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name not in SKIP_DIRS and not p.name.startswith("."))

    for p in walk(root):
        rel = p.relative_to(root).as_posix()
        name = p.name
        ext = p.suffix.lower()
        lang = LANG.get(ext)
        if ENV_FILES.search(rel) and not rel.endswith((".example", ".sample", ".template")):
            cats["env_files"].append(rel)  # never read: may contain secrets
            continue
        size_ok = p.stat().st_size <= 5_000_000
        if lang and size_ok:
            text = read(p)
            n = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
            loc[lang] += n
            files_by_lang[lang] += 1
            if lang in SOURCE_LANGS:
                source_files += 1
        key = False
        if MANIFESTS.match(name):
            text = read(p)
            cats["manifests"].append(rel)
            deps[rel] |= deps_from_manifest(p, text)
            dep_text.append(" ".join(sorted(deps[rel])))
            key = True
        if CONTAINERS.match(name):
            cats["containers"].append(rel)
            key = True
            if "compose" in name:
                text = read(p)
                compose_images |= set(re.findall(r"^\s*image:\s*[\"']?([^\s\"'#]+)", text, re.M))
                m = re.search(r"^services:\s*\n((?:[ \t]+.*\n?|\n)*)", text, re.M)
                if m:
                    compose_services += [s for s in re.findall(r"^  ([A-Za-z0-9_.-]+):\s*$", m.group(1), re.M)]
        if CI_PATHS.search(rel):
            cats["ci_cd"].append(rel)
            key = True
        if DEPLOY_PATHS.search(rel):
            cats["deploy_infra"].append(rel)
            key = True
        elif ext in (".yaml", ".yml") and size_ok and K8S_KIND.search(read(p, 60_000)):
            cats["deploy_infra"].append(rel)
            key = True
        if MIGRATION_DIR.search(rel) and ext in (".py", ".sql", ".rb", ".js", ".ts", ".go", ".xml", ".yaml", ".yml", ".java"):
            cats["migrations"].append(rel)
            key = True
        if SCHEMA_FILES.search(rel):
            cats["schema"].append(rel)
            key = True
        if API_SPECS.search(rel):
            cats["api_specs"].append(rel)
            key = True
        if SECURITY_FILES.search(rel):
            cats["security_files"].append(rel)
            key = True
        if re.search(r"(^|/)(auth|security|permissions?|rbac|acl|middleware)(/|\.|_|$)", rel, re.I) and lang in SOURCE_LANGS:
            cats["auth_code"].append(rel)
            key = True
        if TEST_PATH.search(rel) and lang in SOURCE_LANGS:
            test_files += 1
        if key and size_ok:
            digest = hashlib.sha256(read(p, 5_000_000).encode()).hexdigest()
            key_files[rel] = digest[:16]
            key_hash.update(rel.encode())
            key_hash.update(bytes.fromhex(digest))

    signals = match_signals(" ".join(dep_text) + " " + " ".join(compose_images))
    packages = sorted({str(Path(m).parent) for m in cats["manifests"] if str(Path(m).parent) != "."})
    key_hash.update(json.dumps({"top": top_dirs, "packages": packages}, sort_keys=True).encode())

    inv = {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "repo": root.name,
        "git_commit": git_head(root),
        "fingerprint": key_hash.hexdigest(),
        "size": {"source_files": source_files, "test_files": test_files,
                 "lines_by_language": dict(loc.most_common()), "files_by_language": dict(files_by_lang.most_common())},
        "top_level_dirs": top_dirs,
        "packages": packages,
        "compose_services": sorted(set(compose_services)),
        "compose_images": sorted(compose_images),
        "detected": {k: sorted(v) for k, v in signals.items()},
        "files": {k: sorted(set(v)) for k, v in cats.items()},
        "key_files": dict(sorted(key_files.items())),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(inv, indent=2) + "\n", encoding="utf-8")

    print(f"Inventory of {root.name} -> {out_path}")
    print(f"  commit {inv['git_commit'] or '(no git)'} · {source_files} source files · {test_files} test files")
    top = ", ".join(f"{k} {v:,}" for k, v in list(loc.most_common())[:6])
    print(f"  lines: {top}")
    if packages:
        print(f"  packages/services with their own manifest: {', '.join(packages[:12])}{' …' if len(packages) > 12 else ''}")
    if inv["compose_services"]:
        print(f"  compose services: {', '.join(inv['compose_services'])}")
    for k, v in inv["detected"].items():
        if v:
            print(f"  {k.replace('_', ' ')}: {', '.join(v)}")
    for k, v in inv["files"].items():
        print(f"  {k.replace('_', ' ')}: {len(v)} file(s)" + (" (contents never read)" if k == "env_files" else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
