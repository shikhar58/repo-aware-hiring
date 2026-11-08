# Codebase map — mini-repo
Commit: none · Inventory: 6eabe677d237fff77259255102ce575ddf6bfe85be8b935e4f54994c22591722 · Generated: 2026-11-08

## Overview
A small synthetic orders API used to test map-codebase: one FastAPI service backed by PostgreSQL, packaged as a
container, with a single CI pipeline. About 50 lines of Python.

## Components and services
- **api** (`app/main.py`): FastAPI app exposing a health check and an authenticated orders endpoint; built from
  `Dockerfile` and run as the `api` service in `docker-compose.yml`.
- **db**: PostgreSQL 16 container, the `db` service in `docker-compose.yml`; the api depends on it.

## Data stores and schema
- PostgreSQL only. Access through SQLAlchemy Core with raw SQL text queries (`app/db.py`), connection string from the
  environment.
- Schema managed by plain SQL migration files (`migrations/001_init.sql`), one `orders` table; no migration runner found.

## APIs and integrations
- REST endpoints defined code-first in `app/main.py`: a health check and an orders listing. No API spec file; FastAPI
  generates OpenAPI at runtime. Sentry is the only external service.

## Authentication and security
- JWT bearer tokens verified with HS256 in `app/auth.py`; the signing key comes from an environment variable.
- No password handling, roles or rate limiting found. A local `.env` exists (contents not read).

## CI/CD pipeline
- One GitHub Actions workflow, `.github/workflows/ci.yml`: on every push, install and run pytest. No deployment job,
  no lint or type checks.

## Deployment and infrastructure
- Container image from `Dockerfile`; local orchestration with `docker-compose.yml` (api and db). No IaC or production
  deployment configuration: none found.

## Observability
- Sentry initialised at startup in `app/main.py`; health endpoint for liveness. No metrics or tracing found.

## Testing
- pytest with FastAPI's test client in `tests/test_api.py`; covers only the health check.

## Dependencies
- `pyproject.toml`: FastAPI, SQLAlchemy, psycopg, PyJWT, sentry-sdk; dev extras pytest and httpx.

## Conventions
- Small flat package `app/`; no lint, formatting or type-check configuration found in `pyproject.toml`.

## Hot spots and risks (INTERNAL — never publish)
- `SELECT *` with no pagination in `app/db.py`; no index on `user_id` in `migrations/001_init.sql`.
- No migration runner, no tests for authentication (`tests/test_api.py`).

## Gaps in this map
- Production hosting is not described in the repository.
