# Ana Ferreira
ana.ferreira@example.com · +34 612 345 678 · linkedin.com/in/ana-ferreira-dev · github.com/aferreira-dev
Date of birth: 14/03/1990

## Summary
Backend engineer focused on PostgreSQL-backed Python services.

## Experience
**Senior Backend Engineer, Ledgerly (2020 – present)**
- Owned the PostgreSQL 14 cluster behind the payments API (1.2 TB, 9k writes/s): schema design, indexing strategy and capacity planning.
- Designed zero-downtime migrations with Alembic using expand-contract and batched backfills; added a 200M-row table column and rebuilt indexes with CREATE INDEX CONCURRENTLY.
- Moved migrations out of container start into a dedicated pre-deploy job so 12 API replicas never raced.
- Cut p95 latency of account listing from 900 ms to 40 ms with EXPLAIN ANALYZE, composite indexes and keyset pagination.
- Introduced PgBouncer in transaction mode and pg_stat_statements dashboards for slow-query monitoring.
- Built the test setup for database code: per-test transactions with rollback and Testcontainers in CI.

**Backend Engineer, Shiplane (2016 – 2020)**
- Python services on SQLAlchemy 1.3; tuned relationship loading (selectinload) to remove N+1 queries.
- Wrote Alembic migrations for production data backfills.

## Skills
Python, SQLAlchemy, SQLModel, Alembic, PostgreSQL, PgBouncer, Testcontainers, asyncpg (side project)
