# Codebase map — checkout-svc
Commit: none · Inventory: 72cdd76f7d4ee081f4e0e9a10947f7a6ec9f392a2c676f1d67bf63c2a579590a · Generated: 2026-11-08

## Overview
FastAPI service that places orders and charges customers through the shared acme-payments library. Same template as
billing-svc. Small: one router.

## Components and services
- **API** (`app/main.py`): FastAPI app titled checkout; mounts the orders router.
- **Orders** (`app/api/orders.py`): POST /orders computes an idempotency key and calls `charge` from acme_payments;
  provider failures become HTTP 502.
- **Database session** (`app/db.py`): SQLAlchemy engine and session factory for PostgreSQL.
- Container built from `Dockerfile`; billing-svc calls this service over HTTP.

## Data stores and schema
PostgreSQL through SQLAlchemy (`app/db.py`). Alembic migrations in `alembic/versions/` configured by `alembic.ini`;
only an empty initial revision exists (`alembic/versions/0001_init.py`).

## APIs and integrations
REST: POST /orders (`app/api/orders.py`). Payments via acme-payments (`requirements.txt`, `app/api/orders.py`).

## Authentication and security
None found: no authentication on /orders (`app/api/orders.py`, `app/main.py`). Database URL comes from the
environment (`app/db.py`); a `.env` file exists and was not read.

## CI/CD pipeline
`.github/workflows/ci.yml`: install, pytest, docker build and push of ghcr.io/acme/checkout tagged with the commit.

## Deployment and infrastructure
Container image from `Dockerfile` (uvicorn on port 8000), pushed by `.github/workflows/ci.yml`; deployed by the infra
repo. Environment configuration via `.env` locally (not read).

## Observability
None found: no logging, metrics or tracing set up in `app/`.

## Testing
pytest in `tests/` (`tests/test_orders.py` is a placeholder).

## Dependencies
FastAPI, uvicorn, SQLAlchemy, psycopg, Alembic, httpx and acme-payments pinned in `requirements.txt`.

## Conventions
Routers per resource under `app/api/`; settings from environment variables (`app/db.py`).

## Hot spots and risks (INTERNAL — never publish)
- The idempotency key in `app/api/orders.py` is computed but not passed to `charge`, so retries rely on the library's
  own bucketed key.
- No real tests (`tests/test_orders.py`).

## Gaps in this map
The orders lookup endpoint that billing-svc calls (/orders/by-charge) does not exist in `app/api/orders.py`.
