# Service card — infra
Commit: none · Inventory: 109f5d2e6e444c3b78ffb3610ee6dcd2ec8a8679cb0ffef3db3f90b9e152afc9 · Generated: 2026-11-08 · Level: card

## Overview
Kubernetes manifests for checkout and billing, applied with kustomize on every push to main.

## Components and services
One Deployment and one Service per application: `k8s/checkout.yaml` and `k8s/billing.yaml`, listed in
`k8s/kustomization.yaml`. The Services named checkout and billing give the in-cluster hostnames the apps call.

## Data stores and schema
None found: no database manifests in `k8s/`; databases are managed elsewhere (see Gaps).

## APIs and integrations
None found: no ingress in `k8s/`; services are cluster-internal on port 8000.

## Authentication and security
Secrets come from Kubernetes secrets referenced by name (`k8s/checkout.yaml`); values are not in the repo.

## Deployment and infrastructure
`.github/workflows/deploy.yml` runs kubectl apply -k on `k8s/`. Two replicas each; images pinned to version tags.

## Dependencies
None found: no manifests; uses kubectl and kustomize (`.github/workflows/deploy.yml`).

## Gaps in this card
Where PostgreSQL runs and how secrets are created are not in this repo.
