# System map — acme
Graph: e5a4d9d6b8ba79a8 · Generated: 2026-11-08 · Repos: 4

## Overview
Two FastAPI services (checkout-svc, billing-svc) built from the same template, a shared payments library
(payments-lib, published as acme-payments) that both use to talk to the payment provider, and an infra repo
that deploys both services to Kubernetes. The payment flow crosses all four repos.

## Repositories
| Repo | Tier | Role | Map |
|---|---|---|---|
| payments-lib | primary | library: charges, refunds, idempotency | full map |
| checkout-svc | primary | service: places orders and charges | full map |
| billing-svc | supporting | service: invoices and refunds | service card |
| infra | supporting | deploys checkout and billing to Kubernetes | service card |

## Connections
- checkout-svc → payments-lib: depends on acme-payments 2.3.0; calls `charge` and `idempotency_key` when placing an order.
- billing-svc → payments-lib: depends on acme-payments 2.3.0; calls `refund` for invoice refunds.
- billing-svc → checkout-svc: HTTP call to http://checkout:8000 to look up the order for a charge; the hostname is the
  Kubernetes Service declared in infra. No authentication between the services.
- infra → checkout-svc: deploys image ghcr.io/acme/checkout built by checkout-svc's CI.
- infra → billing-svc: deploys image ghcr.io/acme/billing built by billing-svc's CI.
- payments-lib publishes to the internal package index pypi.acme.internal (not a repo in this workspace).

## Shared code and templates
checkout-svc and billing-svc share one template (same layout, FastAPI + SQLAlchemy + Alembic, same CI and Dockerfile);
checkout-svc's full map explains the shared structure and billing-svc's card lists only differences. Shared code is
the acme-payments package, versioned and pinned to the same release in both services.

## Ownership and team boundaries
Unknown: the hiring manager hasn't said who owns each repo. Assumed for now that the payments team owns payments-lib
and checkout-svc, and a platform team owns infra (recorded as assumptions in decisions.json).

## Gaps
Where PostgreSQL runs and how provider credentials reach the services are not visible in any repo here.
The endpoint billing-svc calls on checkout-svc does not exist yet in checkout-svc.
