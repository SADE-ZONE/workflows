# Idempotency Recommendations (Client Integrations)

**Last Updated On:** 2026-04-22

These are integration recommendations for Operator, SafeCert, and tracker/telemetry clients calling SADE APIs.

## Where idempotency is required

Provide `idempotency_key` on these routes:

1. `POST /entry-request`
2. `POST /attestation-submission`

For `POST /exit-request` and `POST /tracker-session-finalized`, SADE deduplicates by `flight_session_id` instead of requiring a separate `idempotency_key` field.

## How SADE deduplicates

SADE deduplicates by:

- `(handler_name, idempotency_key)`

Behavior:

1. Same key + same payload => cached response (safe retry).
2. Same key + different payload => request is rejected as failed business outcome.
3. Duplicate arrives while first request is still processing => request is rejected as failed business outcome.

## Key generation recommendations

1. Use UUIDv4 for each logical request.
2. Keep keys opaque (do not encode mutable business fields into key format).
3. Persist key with the outbound request in your caller so retries reuse the same key.

Example key:

- `f47ac10b-58cc-4372-a567-0e02b2c3d479`

## Retry rules for clients

1. If network/timeout happens and you are retrying the same logical message, retry with the exact same payload and exact same `idempotency_key`.
2. For `POST /exit-request`, retry with the exact same payload and same `flight_session_id`.
3. For `POST /tracker-session-finalized`, retry with the exact same payload and same `flight_session_id`.
4. If any payload field changes, generate a new key for the endpoints that use explicit `idempotency_key`.
5. Do not recycle old keys for unrelated requests.

## TTL behavior

Current idempotency record TTL is 24 hours.

Implication:

- Reusing a key after TTL expiry is treated as a new request.

## Suggested logging fields on your side

Include these in caller logs for incident debugging:

1. `idempotency_key`
2. HTTP method + path
3. request hash or payload fingerprint
4. response status and response body
5. `flight_session_id` for exit-request and tracker finalization calls

This makes duplicate/retry analysis fast when integrating across teams.
