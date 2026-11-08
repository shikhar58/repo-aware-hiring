# Codebase map — payments-lib
Commit: none · Inventory: 1d749ae4bd28a8428945b5b6cbc0d96b49ec63c75328aed927b04bc0afcd21fc · Generated: 2026-11-08

## Overview
A small shared Python library, published as the package `acme-payments` (`pyproject.toml`), that wraps the external
payment provider: charges, refunds and idempotency keys. Used by checkout-svc and billing-svc. Pydantic models.

## Components and services
- **acme_payments** (`src/acme_payments/`): one package. `src/acme_payments/client.py` holds `PaymentClient` (HTTP client
  over httpx) plus module-level `charge` and `refund` helpers backed by a lazily created default client.
  `src/acme_payments/idempotency.py` derives idempotency keys from customer, amount and a 60-second time bucket.
- The package calls the provider at api.payments-provider.com over HTTPS; no other services.

## Data stores and schema
None found: the library keeps no state (checked `src/acme_payments/` for database or cache clients). `Charge` is a
Pydantic response model in `src/acme_payments/client.py`, not a stored entity.

## APIs and integrations
Outbound only: POST /charges and /charges/{id}/refunds on the provider (`src/acme_payments/client.py`), with an
`Idempotency-Key` header on charges. Public Python API exported in `src/acme_payments/__init__.py`.

## Authentication and security
None found in code: the client sends no credentials itself (`src/acme_payments/client.py`), so authentication with the
provider must be configured by callers or a proxy; see Gaps. Idempotency keys reduce double charges on retries.

## CI/CD pipeline
`.github/workflows/publish.yml`: on version tags, installs dependencies, runs pytest, builds the package and uploads it
to the internal package index at pypi.acme.internal.

## Deployment and infrastructure
Not deployed itself: it ships as a package to the internal index (`.github/workflows/publish.yml`) and runs inside the
services that install it. No containers found.

## Observability
None found: no logging, metrics or tracing in `src/acme_payments/`; errors surface as httpx exceptions to callers.

## Testing
pytest in `tests/` (`tests/test_client.py` covers idempotency key stability). respx is a test dependency for mocking
HTTP but no HTTP tests exist yet.

## Dependencies
httpx and pydantic at runtime, pytest and respx for tests (`pyproject.toml`). Version 2.3.0.

## Conventions
src layout (`src/acme_payments/`), type hints throughout, explicit `__all__` in `src/acme_payments/__init__.py`.

## Hot spots and risks (INTERNAL — never publish)
- The 60-second idempotency bucket in `src/acme_payments/idempotency.py` can let a retry that crosses a bucket boundary
  charge twice.
- The module-level default client in `src/acme_payments/client.py` is shared global state with no timeout override.
- No tests for charge or refund paths (`tests/`).

## Gaps in this map
Provider authentication is not visible here; it may be configured in the services or the infrastructure repo.
