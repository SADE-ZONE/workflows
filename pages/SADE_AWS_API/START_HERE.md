# Client Integration Start Here

Status date: 2026-03-09

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

`http://sarec-sade-use2-api-alb-1413405053.us-east-2.elb.amazonaws.com`

## Current unfinished/stubbed behavior to note

This environment is usable for integration testing, but these components are still stubbed:

1. Environmental conditions service: currently returns hardcoded/synthetic data.
2. Flight tracker integration: stop/finalization behavior is simulated (no external telemetry provider wired yet).
3. Decision Maker: currently uses a temporary stub service (including `test_overrides` hooks such as `force_decision`).
