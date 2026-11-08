# Hiring brief — Backend Engineer, Database Owner
Date: 2026-11-08 · Owner: Dry-run hiring manager · Status: approved
Repo: fastapi/full-stack-fastapi-template (public, used as a stand-in for "our" codebase)

<!-- Dry-run note: produced by following hiring-plan. The hiring manager's answers below were
     simulated; each question was asked one at a time with multiple-choice options. -->

## Planning conversation (summary)
1. Mission type → **Area ownership** (database layer), with an expected scaling phase.
2. Scope → confirmed `backend/app/models.py`, `backend/app/crud.py`, `backend/app/core/db.py`,
   `backend/app/alembic/`, `backend/tests/conftest.py`, the `db` service in `compose.yml`.
3. Outcome in 6 months → "Safe zero-downtime migrations and query performance we can measure"
   (chosen over "move to async SQLAlchemy" and "multi-tenant schema").
4. Autonomy → leads the area alone; reviews from the backend lead.
5. Constraints → permanent, remote within EU time zones (did not change the role design further).
6. Team context → team is strong on FastAPI/API design and frontend; nobody owns Postgres operations.

## Mission
Own the backend's persistence layer: make schema changes safe to ship to production without
downtime, make query performance observable and fast as data grows, and make database tests reliable.

## Scope in the repo
- `backend/app/models.py` — SQLModel tables (User, Item) with UUID keys, cascade deletes
- `backend/app/crud.py`, `backend/app/api/routes/*.py` — query patterns, pagination
- `backend/app/core/db.py` — sync engine, default pool settings
- `backend/app/alembic/` — 5 migrations incl. an integer→UUID data migration
- `backend/scripts/prestart.sh` — runs `alembic upgrade head` on every container start
- `backend/tests/conftest.py` — one session-scoped DB fixture, cleanup only at the end
- `compose.yml` — single Postgres 18 container, no backup or replica config

## What we found
- Migrations run automatically at container start (`backend/scripts/prestart.sh`); with several
  replicas this races and couples deploys to schema changes.
- Item listing uses offset pagination ordered by `created_at` (`backend/app/api/routes/items.py`);
  `item.owner_id` and `created_at` have no explicit index in `backend/app/models.py`.
- A previous migration rewrote primary keys to UUID in place
  (`backend/app/alembic/versions/d98dd8ec85a3_*.py`): risky on large tables, a sign this kind of work recurs.
- Tests share one database for the whole session with no per-test transaction rollback
  (`backend/tests/conftest.py`), so tests can leak state into each other.
- Sync SQLAlchemy engine with default pool (`backend/app/core/db.py`); no pooler such as PgBouncer.
- No backup, replication or monitoring config for Postgres (`compose.yml`).
- The codebase is small (~2k lines of Python). Most demands come from where the product is going,
  not from current complexity, so requirements below lean on the mission, not on the code size.

## Success looks like
- 3 months: migrations decoupled from app start; per-test isolation; slow-query visibility.
- 6 months: zero-downtime migration playbook used on real changes; key queries indexed and measured.
- 12 months: backups/restore tested, pooling in place, a plan for read scaling if needed.

## Chosen role shape
**A. Backend engineer with deep PostgreSQL ownership** (chosen).
Rejected: B. Dedicated DBA (too ops-only for a small team); C. Contractor for an audit + upskill
an internal engineer (would leave nobody owning the area long term).

## Requirements derived from the mission
| Requirement | Why | Must-have? |
|---|---|---|
| Runs PostgreSQL in production: schema design, indexes, query plans | ownership of the area | yes |
| Ships schema/data migrations on live data safely | prestart.sh coupling; UUID rewrite history | yes |
| Diagnoses and fixes query performance | offset pagination, missing indexes | no (important) |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | the codebase | no (important) |
| Reliable database test setups | conftest.py shared state | no (important) |
| Zero-downtime deploy practices with multiple replicas | prestart.sh race | no (important) |
| Postgres operations: backups, pooling, monitoring | compose.yml gaps | no (important) |
| Async database access | possible future scaling | no (nice) |

## Transferable backgrounds we welcome
Django ORM, Rails ActiveRecord, Hibernate/JPA, Go with pgx/sqlc; Flyway, Liquibase, goose,
Django or Rails migrations; DBAs who write application code.

## Anti-goals
- Not a data engineer or analytics role (warehouses, dbt, Spark are not credited for must-haves).
- Not a frontend role. Not hiring for FastAPI expertise: the team already has it.
- Do not screen on years of experience, degree or employer prestige.

## Open questions
- Is a managed Postgres service planned? (affects how much ops depth matters)
