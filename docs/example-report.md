# Screening report — Backend Engineer, Database Owner

Rubric v1 · approved by Dry-run hiring manager · 2026-11-09 · 12 candidates

> **Decision support only.** This report ranks CV evidence against an approved rubric.
> It does not reject or advance anyone. A qualified person must review each candidate's
> evidence, can change any result, and is responsible for the decision. Candidates who are the
> subject of a decision must be told that AI was used. "No evidence" means the CV does not show
> it, not that the candidate lacks it: use the interview probes.

**Human review.** Reviewer: not yet recorded (record a qualified reviewer before any decision).

**Candidates told AI was used:** not confirmed (required before any decision).

## Shortlist

| Rank | Candidate | File | Score /100 | Must-haves | Confidence | Flags |
|---|---|---|---|---|---|---|
| 1 | C01 | ana-ferreira.md | 88.3 | pass | medium |  |
| 2 | C10 | rahul-mehta.docx | 56.7 | pass | medium |  |
| 3 | C08 | mei-chen.md | 46.7 | pass | medium |  |
| 4 | C07 | liam-obrien.md | 45.0 | pass | medium |  |
| =5 | C02 | arjun-rao.pdf | 40.0 | pass | high |  |
| =5 | C04 | elena-petrova.md | 40.0 | pass | medium | ⚠ injection |
| 7 | C12 | tom-becker.md | 26.7 | pass | medium |  |
| 8 | C06 | james-okafor.md | 18.3 | pass | high |  |
| 9 | C11 | sofia-rossi.md | 6.7 | pass | high |  |
| 10 | C03 | daniel-kowalski.md | 6.7 | verify: Runs PostgreSQL in production (schema design, indexes, query plans), Ships schema and data migrations on live data safely | medium |  |
| 11 | C09 | priya-nair.pdf | 5.0 | verify: Runs PostgreSQL in production (schema design, indexes, query plans), Ships schema and data migrations on live data safely | medium | ⚠ injection |

**Below the line** (CV contradicts a must-have; unranked):

- C05 — fatima-alsayed.md — fails: Runs PostgreSQL in production (schema design, indexes, query plans)

## Rubric gaps worth noticing

- The job is defined by the brief's mission; the codebase is small, so criteria come from the gaps it shows (migrations at app start, no test isolation, no backups).
- FastAPI expertise is deliberately not screened for: the team already has it.

## Candidate detail

### C01 — ana-ferreira.md — 88.3/100

**Strengths**
- Has already solved our exact prestart.sh migration race
- Measured query-performance wins with keyset pagination

**Gaps / no evidence**
- No evidence of backups/replication or restore drills

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 3/3 | evidenced | “Owned the PostgreSQL 14 cluster behind the payments API (1.2 TB, 9k writes/s): schema design, indexing strategy and capacity planning” |
| Ships schema and data migrations on live data safely | must-have | 3/3 | evidenced | “Designed zero-downtime migrations with Alembic using expand-contract and batched backfills” |
| Diagnoses and fixes query performance | important | 3/3 | evidenced | “Cut p95 latency of account listing from 900 ms to 40 ms with EXPLAIN ANALYZE, composite indexes and keyset pagination” |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 3/3 | evidenced | “tuned relationship loading (selectinload) to remove N+1 queries” |
| Builds reliable database test setups | important | 3/3 | evidenced | “Built the test setup for database code: per-test transactions with rollback and Testcontainers in CI” |
| Zero-downtime deploys with schema changes and multiple replicas | important | 3/3 | evidenced | “Moved migrations out of container start into a dedicated pre-deploy job so 12 API replicas never raced” |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 2/3 | evidenced | “Introduced PgBouncer in transaction mode and pg_stat_statements dashboards for slow-query monitoring” |
| Async database access | nice-to-have | 1/3 | weak | “asyncpg (side project)” |

**Interview probes (grounded in our repo)**
1. Our backend runs `alembic upgrade head` in prestart.sh on every container. Walk through moving that to a pre-deploy job.
2. items.py uses OFFSET pagination ordered by created_at. How would you change the query and indexes?

**Flags:** none

---

### C10 — rahul-mehta.docx — 56.7/100

**Strengths**
- Deep Postgres ownership incl. operations our compose.yml lacks
- Online migrations

**Gaps / no evidence**
- Java/Hibernate rather than Python

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 3/3 | evidenced | “Owned production PostgreSQL 13 for the lending platform: schema design, indexing and query plan reviews for all teams” |
| Ships schema and data migrations on live data safely | must-have | 3/3 | evidenced | “Wrote Flyway migrations on live data, using expand-contract changes and batched updates to avoid long locks” |
| Diagnoses and fixes query performance | important | 3/3 | evidenced | “Tuned slow queries with EXPLAIN ANALYZE and pg_stat_statements; partitioned the payments table by month” |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 1/3 | weak | “Java services with Hibernate/JPA” |
| Builds reliable database test setups | important | 2/3 | evidenced | “integration tests with Testcontainers” |
| Zero-downtime deploys with schema changes and multiple replicas | important | 0/3 | no evidence | — |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 3/3 | evidenced | “Set up streaming replication, PgBouncer and nightly backups with tested restores” |
| Async database access | nice-to-have | 0/3 | no evidence | — |

**Interview probes (grounded in our repo)**
1. What would you set up first for backups and pooling given our single Postgres container in compose.yml?

**Flags:** none

---

### C08 — mei-chen.md — 46.7/100

**Strengths**
- Batched backfills at very large scale
- Backward-compatible deploys

**Gaps / no evidence**
- Go rather than Python; would need to ramp on SQLAlchemy/SQLModel

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 2/3 | evidenced | “Designed PostgreSQL schemas and indexes for an event ingestion service” |
| Ships schema and data migrations on live data safely | must-have | 3/3 | evidenced | “Wrote goose migrations for production, including batched backfills on tables with 1B rows” |
| Diagnoses and fixes query performance | important | 2/3 | evidenced | “Profiled queries with EXPLAIN ANALYZE and pg_stat_statements; replaced OFFSET pagination with keyset pagination” |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 1/3 | weak | “Go, pgx, sqlc”; “Python (scripting)” |
| Builds reliable database test setups | important | 2/3 | evidenced | “Integration tests against ephemeral Postgres containers in CI” |
| Zero-downtime deploys with schema changes and multiple replicas | important | 2/3 | evidenced | “Ran blue-green deploys where schema changes shipped one release ahead of the code that used them” |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 0/3 | no evidence | — |
| Async database access | nice-to-have | 1/3 | weak | “pgx” |

**Interview probes (grounded in our repo)**
1. Our items listing uses OFFSET; you replaced that before. How would you do it with SQLModel?

**Flags:** none

---

### C07 — liam-obrien.md — 45.0/100

**Strengths**
- Lock-aware migrations on a large table
- Transactional tests

**Gaps / no evidence**
- Django ORM rather than SQLAlchemy (transferable)
- No operations evidence

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 2/3 | evidenced | “Maintained a Django monolith on PostgreSQL with 40 tables and 300M rows in the largest table” |
| Ships schema and data migrations on live data safely | must-have | 3/3 | evidenced | “Wrote Django migrations for production data, including a three-step rename of a heavily used column to avoid locking” |
| Diagnoses and fixes query performance | important | 2/3 | evidenced | “Added partial and composite indexes after reading EXPLAIN output for the slowest endpoints; reduced report generation from 30 s to 4 s” |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 2/3 | evidenced | “Django ORM” |
| Builds reliable database test setups | important | 2/3 | evidenced | “Used pytest-django with transactional tests and factory fixtures for all database code” |
| Zero-downtime deploys with schema changes and multiple replicas | important | 1/3 | weak | “took part in weekly deployments that included schema changes” |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 0/3 | no evidence | — |
| Async database access | nice-to-have | 0/3 | no evidence | — |

**Interview probes (grounded in our repo)**
1. Map your three-step column rename onto Alembic for our item table. What runs in which deploy?

**Flags:** none

---

### C02 — arjun-rao.pdf — 40.0/100

**Strengths**
- Same Python/SQLAlchemy/Alembic toolchain we use
- Production data backfills

**Gaps / no evidence**
- MySQL rather than PostgreSQL
- No evidence on deploy safety or database operations

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 1/3 | weak | “Python services with SQLAlchemy on MySQL 8; designed tables and indexes for the orders service” |
| Ships schema and data migrations on live data safely | must-have | 2/3 | evidenced | “Wrote Alembic migrations for production, including a data backfill run in batches overnight” |
| Diagnoses and fixes query performance | important | 2/3 | evidenced | “Fixed N+1 queries with joinedload and added covering indexes after EXPLAIN” |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 2/3 | evidenced | “Python services with SQLAlchemy on MySQL 8” |
| Builds reliable database test setups | important | 2/3 | evidenced | “pytest suite with a MySQL container in CI” |
| Zero-downtime deploys with schema changes and multiple replicas | important | 0/3 | no evidence | — |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 0/3 | no evidence | — |
| Async database access | nice-to-have | 0/3 | no evidence | — |

**Interview probes (grounded in our repo)**
1. Which PostgreSQL features would you miss coming from MySQL, e.g. for the UUID rewrite in our d98dd8ec85a3 migration?

**Flags:** none

---

### C04 — elena-petrova.md — 40.0/100

**Strengths**
- Directly relevant stack
- Per-test rollback fixes our conftest.py shared-state problem

**Gaps / no evidence**
- No evidence on zero-downtime deploys or operations

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 2/3 | evidenced | “Production Python services with SQLAlchemy 2.0 and PostgreSQL”; “Added indexes for slow queries found with EXPLAIN” |
| Ships schema and data migrations on live data safely | must-have | 2/3 | evidenced | “Wrote Alembic migrations with data backfills for production tables” |
| Diagnoses and fixes query performance | important | 2/3 | evidenced | “Added indexes for slow queries found with EXPLAIN; moved list endpoints to keyset pagination” |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 2/3 | evidenced | “Production Python services with SQLAlchemy 2.0 and PostgreSQL” |
| Builds reliable database test setups | important | 2/3 | evidenced | “Pytest fixtures with per-test transaction rollback” |
| Zero-downtime deploys with schema changes and multiple replicas | important | 0/3 | no evidence | — |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 0/3 | no evidence | — |
| Async database access | nice-to-have | 0/3 | no evidence | — |

**Interview probes (grounded in our repo)**
1. Our conftest.py shares one DB session for the whole test run. How would you introduce per-test rollback without slowing CI?

**Flags:** possible_prompt_injection: summary contains a note addressed to the AI recruiting system; ignored for scoring

---

### C12 — tom-becker.md — 26.7/100

**Strengths**
- Strongest operations background in the pool

**Gaps / no evidence**
- Little application-side ORM or query work

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 2/3 | evidenced | “Ran PostgreSQL HA clusters with Patroni and etcd” |
| Ships schema and data migrations on live data safely | must-have | 1/3 | weak | “Reviewed and ran application teams' schema migrations during deployments” |
| Diagnoses and fixes query performance | important | 0/3 | no evidence | — |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 1/3 | weak | “Python tooling for automation (no ORM)” |
| Builds reliable database test setups | important | 0/3 | no evidence | — |
| Zero-downtime deploys with schema changes and multiple replicas | important | 1/3 | weak | “Reviewed and ran application teams' schema migrations during deployments” |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 3/3 | evidenced | “Backups and point-in-time recovery with pgBackRest; monthly restore drills” |
| Async database access | nice-to-have | 0/3 | no evidence | — |

**Interview probes (grounded in our repo)**
1. Our app runs migrations at container start. From an SRE view, what breaks first with multiple replicas?

**Flags:** none

---

### C06 — james-okafor.md — 18.3/100

**Strengths**
- Knows our exact framework stack

**Gaps / no evidence**
- Junior; migrations only autogenerated on staging
- No performance or operations evidence

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 1/3 | weak | “Built CRUD endpoints with FastAPI and SQLModel on PostgreSQL” |
| Ships schema and data migrations on live data safely | must-have | 1/3 | weak | “Generated Alembic migrations with autogenerate for new tables in the staging environment” |
| Diagnoses and fixes query performance | important | 0/3 | no evidence | — |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 2/3 | evidenced | “Built CRUD endpoints with FastAPI and SQLModel on PostgreSQL” |
| Builds reliable database test setups | important | 1/3 | weak | “Wrote pytest tests for the API, using a shared test database” |
| Zero-downtime deploys with schema changes and multiple replicas | important | 0/3 | no evidence | — |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 0/3 | no evidence | — |
| Async database access | nice-to-have | 0/3 | no evidence | — |

**Interview probes (grounded in our repo)**
1. Alembic autogenerate produced our d98dd8ec85a3 UUID migration by hand-editing. What would you check before running it on production?

**Flags:** none

---

### C11 — sofia-rossi.md — 6.7/100

**Strengths**
- Full-stack delivery

**Gaps / no evidence**
- Frontend-focused; database work is light
- Frontend is an anti-goal for this role

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 1/3 | weak | “Small Node.js API with Prisma on a managed PostgreSQL database” |
| Ships schema and data migrations on live data safely | must-have | 1/3 | weak | “ran prisma migrate for new tables” |
| Diagnoses and fixes query performance | important | 0/3 | no evidence | — |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 1/3 | weak | “Node.js API with Prisma” |
| Builds reliable database test setups | important | 0/3 | no evidence | — |
| Zero-downtime deploys with schema changes and multiple replicas | important | 0/3 | no evidence | — |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 0/3 | no evidence | — |
| Async database access | nice-to-have | 0/3 | no evidence | — |

**Interview probes (grounded in our repo)**
1. Describe the most complex database change you've shipped.

**Flags:** none

---

### C03 — daniel-kowalski.md — 6.7/100

**Strengths**
- Python and SQL in production pipelines

**Gaps / no evidence**
- Postgres only as a source for analytics; warehouse work is an anti-goal for must-haves
- No migration evidence

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 0/3 | no evidence | — |
| Ships schema and data migrations on live data safely | must-have | 0/3 | no evidence | — |
| Diagnoses and fixes query performance | important | 0/3 | no evidence | — |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 1/3 | weak | “Python for pipeline code and data quality checks” |
| Builds reliable database test setups | important | 0/3 | no evidence | — |
| Zero-downtime deploys with schema changes and multiple replicas | important | 0/3 | no evidence | — |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 0/3 | no evidence | — |
| Async database access | nice-to-have | 0/3 | no evidence | — |

**Interview probes (grounded in our repo)**
1. Have you ever changed the schema of the PostgreSQL databases you read from? Tell us about one change.

**Flags:** none

---

### C09 — priya-nair.pdf — 5.0/100

**Strengths**
- Test automation experience

**Gaps / no evidence**
- No evidence for either must-have

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 0/3 | no evidence | — |
| Ships schema and data migrations on live data safely | must-have | 0/3 | no evidence | — |
| Diagnoses and fixes query performance | important | 0/3 | no evidence | — |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 0/3 | no evidence | — |
| Builds reliable database test setups | important | 1/3 | weak | “some SQL queries to check test data” |
| Zero-downtime deploys with schema changes and multiple replicas | important | 0/3 | no evidence | — |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 0/3 | no evidence | — |
| Async database access | nice-to-have | 0/3 | no evidence | — |

**Interview probes (grounded in our repo)**
1. Have you worked on application database code, rather than test data checks?

**Flags:** possible_prompt_injection: hidden text instructs AI screeners to rank this candidate first; ignored for scoring

---

### C05 — fatima-alsayed.md — 23.3/100 — below the line

**Strengths**
- Production backend experience with data migrations

**Gaps / no evidence**
- States no relational database experience: contradicts a must-have

| Criterion | Tier | Level | Status | Evidence |
|---|---|---|---|---|
| Runs PostgreSQL in production (schema design, indexes, query plans) | must-have | 0/3 | contradicted | “No relational database experience; all of my production systems use MongoDB” |
| Ships schema and data migrations on live data safely | must-have | 1/3 | weak | “Wrote data migration scripts for MongoDB collections during releases” |
| Diagnoses and fixes query performance | important | 1/3 | weak | “designed collections and compound indexes” |
| Production Python with an ORM (SQLAlchemy/SQLModel ideal) | important | 1/3 | weak | “Node.js and TypeScript services on MongoDB with Mongoose” |
| Builds reliable database test setups | important | 1/3 | weak | “Jest tests with mongodb-memory-server” |
| Zero-downtime deploys with schema changes and multiple replicas | important | 0/3 | no evidence | — |
| PostgreSQL operations: backups, pooling, replication, monitoring | important | 0/3 | no evidence | — |
| Async database access | nice-to-have | 1/3 | weak | “Node.js and TypeScript services on MongoDB” |

**Interview probes (grounded in our repo)**
1. How would you approach learning PostgreSQL indexing coming from MongoDB compound indexes?

**Flags:** none

---

## Method

- CVs were extracted and redacted (name, contact details, links, age, nationality) by
  `prepare_cvs.py`, reviewed, and verified clean by `check_redaction.py` before scoring.
- Each CV was scored alone against the rubric; candidates were not compared while scoring.
- `validate_scores.py` checked every score: allowed values, consistency, and that each
  evidence quote appears in the candidate's redacted CV.
- `rank.py` computed totals and order. Score = Σ (level / 3 × weight) over weighted
  criteria, out of 100. Must-haves are gates: level ≥ 1 passes; *no evidence* → "verify"
  (ranked after all passing candidates); *contradicted* → below the line.
- Equal scores are shown as ties (=N).
