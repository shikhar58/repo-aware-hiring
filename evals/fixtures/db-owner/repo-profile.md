# Repo profile — full-stack-fastapi-template — Database owner
Generated: 2026-11-08 · Scope: backend/app (models, crud, core/db, alembic, routes), backend/tests, compose.yml · Commit: see clone

## Stack
| Technology | Centrality | Evidence |
|---|---|---|
| Python 3.14 | core | backend/pyproject.toml (`requires-python >=3.14`) |
| FastAPI | core | backend/app/main.py, backend/app/api/ |
| SQLModel (SQLAlchemy 2 + Pydantic) | core | backend/app/models.py, backend/app/crud.py |
| PostgreSQL 18, psycopg 3 | core | compose.yml `db` service; backend/pyproject.toml |
| Alembic | core | backend/app/alembic/, backend/scripts/prestart.sh |
| pytest + coverage (90% gate) | regular | backend/tests/, .github/workflows/test-backend.yml |
| mypy strict, ruff, ty | regular | backend/pyproject.toml |
| Docker Compose | regular | compose.yml |
| Sentry | incidental | backend/pyproject.toml |

## Architecture
- Single FastAPI service, sync request handlers using a shared SQLAlchemy engine (backend/app/core/db.py).
- Session injected per request via dependency (backend/app/api/deps.py).
- Two tables, User and Item, UUID keys, cascade delete owner→items (backend/app/models.py).
- Schema managed only through Alembic; `create_all` disabled (backend/app/core/db.py comments).
- Migrations applied at container start before the app runs (backend/scripts/prestart.sh).

## Conventions & quality bar
- Strict typing (mypy strict, ty with error-on-warning) — backend/pyproject.toml.
- Coverage must stay ≥ 90% in CI — .github/workflows/test-backend.yml.
- Tests run against a real Postgres in Docker, not SQLite — test-backend.yml (`docker compose up -d --wait db`).
- CRUD helpers take keyword-only `session` arguments — backend/app/crud.py.

## Hard problems a new hire will meet
- Migrations coupled to app start: concurrent replicas race; rollbacks are manual (backend/scripts/prestart.sh).
- In-place primary key type change done once already (backend/app/alembic/versions/d98dd8ec85a3_*.py).
- Offset pagination + count(*) per request, ordered by unindexed `created_at` (backend/app/api/routes/items.py).
- Shared session-scoped test DB without per-test rollback (backend/tests/conftest.py).
- No pooling, backup, replication or slow-query monitoring (compose.yml, backend/app/core/db.py).

## Mission lens
For database ownership the relevant code is small (~2k lines Python in total; 5 migrations).
The role's difficulty is in practices the code does not have yet: online migrations, indexing
strategy, test isolation, operations. Rubric criteria should come mainly from the brief's
mission and these gaps, and must not reward familiarity with this tiny codebase.

## Transferable vs. specific
- Transfers well: any production Postgres work; Django/Rails/Hibernate/Go DB access; Flyway,
  Liquibase, goose, Django or Rails migrations; pytest-like transactional fixtures in any language.
- Stack-specific (learnable in weeks): SQLModel API, Alembic CLI, FastAPI dependency injection.
