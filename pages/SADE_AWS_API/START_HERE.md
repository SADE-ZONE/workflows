# Client Integration Start Here

Status date: 2026-05-28

If you are integrating with the deployed SADE AWS API, read these in order:

1. [`OPERATOR_LIFECYCLE.md`](./OPERATOR_LIFECYCLE.md)
2. [`API_REFERENCE.md`](./API_REFERENCE.md)
3. [`IDEMPOTENCY_RECOMMENDATIONS.md`](./IDEMPOTENCY_RECOMMENDATIONS.md)

## What each document gives you

1. Lifecycle: operational sequence (registry -> entry -> action-required path -> exit request -> tracker finalization).
2. API reference: exact routes, payload expectations, and response semantics.
3. Idempotency: retry-safe calling patterns and key management rules.

## Base URL

Current AWS base URL:

`https://api.sadezone.org`

Public API calls to this base URL require HTTPS mTLS with a SADE-issued client certificate and private key.

## Current integration behavior to note

This environment is usable for integration testing, with these caveats:

1. Environmental conditions service: may still return hardcoded/synthetic data depending on environment.
2. Decision Maker and Flight Monitor support `test_overrides` hooks for deterministic integration tests.
3. Flight Monitor can run its normal telemetry path; fake/no-drone tests should include `test_overrides.flight_monitor` so sessions close automatically.
