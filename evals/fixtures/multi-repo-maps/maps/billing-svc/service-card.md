# Service card — billing-svc
Commit: none · Inventory: e314d0984aff6d45abc8e27b618a6c3c1995fb2530ea869d1fb5788f726e43b1 · Generated: 2026-11-08 · Level: card

## Overview
FastAPI service for invoices and refunds. Same template as checkout-svc (see its map); only differences are noted here.

## Components and services
- **Invoices** (`app/api/invoices.py`): POST /invoices/{id}/refund looks up the order in checkout-svc over HTTP
  (`checkout:8000`) and refunds through acme_payments. App entry `app/main.py`; container from `Dockerfile`.

## Data stores and schema
PostgreSQL via SQLAlchemy (`app/db.py`), Alembic migrations in `alembic/versions/` (`alembic.ini`), as in checkout-svc.

## APIs and integrations
REST: POST /invoices/{id}/refund (`app/api/invoices.py`); calls checkout-svc and acme-payments (`requirements.txt`).

## Authentication and security
None found on the endpoint (`app/api/invoices.py`); service-to-service call has no auth. `.env` exists, not read.

## Deployment and infrastructure
Image ghcr.io/acme/billing built and pushed by `.github/workflows/ci.yml` from `Dockerfile`; deployed by infra.

## Dependencies
Same as checkout-svc, including acme-payments (`requirements.txt`).

## Gaps in this card
Testing, CI details and observability not covered at card level.
