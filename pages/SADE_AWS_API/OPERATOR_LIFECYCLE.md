# Operator Lifecycle Guide (AWS Runtime)

**Last Updated On:** 2026-08-12

This guide is the practical sequence for operator-facing testing and integration.

Base URL used below:

`https://api.sadezone.org`

## 1) Create registry records first

Before requesting entry, seed all required registry records:

1. `POST /registry/uav-model`
2. `POST /registry/uav`
3. `POST /registry/pilot`
4. `POST /registry/zone`

If any required registry record is missing, `/entry-request` is rejected at admission.

## 2) Submit entry request

Call:

- `POST /entry-request`

Possible outcomes:

1. HTTP `202` with `status: "ACCEPTED"` and a `status_url`
2. HTTP `409` with `status: "REJECTED"` and a `failure_code`

Entry-window admission rules:

1. `requested_exit_time_utc` must be in the future.
2. `requested_entry_time_utc` may be at most 5 minutes in the past.
3. Requests outside those bounds are rejected before entering the async workflow.

After acceptance, read `GET /entry-requests/{evaluation_series_id}` using the `status_url`.
If the workflow becomes action-required, the status response will include `action_required.action_id`.

Optional MQTT notifications:

1. Include `notifications.entry_request_updates.enabled=true` on `POST /entry-request` to request operator notifications.
2. If accepted, the receipt will include `notifications.entry_request_updates.topic`.
3. Subscribe to that exact topic if you want the retained latest summary for this workflow.
4. MQTT notifications are convenience signals only; `GET /entry-requests/{evaluation_series_id}` remains the authoritative state source.
5. SADE does not publish an MQTT message for the initial `ACCEPTED` receipt state. Current publishable entry outcomes are:
   - `APPROVED`
   - `APPROVED_CONSTRAINTS`
   - `ACTION_REQUIRED`
   - `DENIED`

Why this is asynchronous by design:

1. Entry evaluation can take variable time even before SafeCert is involved.
2. The decision adapter may be backed by an LLM or other external reasoning engine, and those calls can be slow, bursty, or temporarily unavailable.
3. If the decision becomes `ACTION_REQUIRED`, the workflow pauses for attestation. That introduces a human-in-the-loop dependency because evidence may need to be gathered, reviewed, and submitted later rather than immediately.
4. Holding the original HTTP request open across those stages would make SADE vulnerable to request timeouts, load balancer timeouts, client disconnects, retry storms, and inconsistent user experience when downstream services respond slowly.
5. Returning a `status_url` instead lets SADE run the workflow asynchronously and event-driven internally while giving operators one stable place to check progress.
6. In a UI, this becomes a simple status page or dashboard refresh problem rather than a long-lived request problem.

## 3) Force decisions for testing

In top-level `test_overrides.decision_maker`, set `force_decision` to drive deterministic test behavior.

Supported values:

1. `APPROVED`
2. `APPROVED_CONSTRAINTS`
3. `DENIED`
4. `ACTION_REQUIRED`
5. `NONE` (simulates Decision Maker returning no usable result, returns failed business outcome)
6. `RAISE` (simulates Decision Maker processing failure, returns failed business outcome)

Example snippet:

```json
{
  "test_overrides": {
    "decision_maker": {
      "force_decision": "ACTION_REQUIRED",
      "evidence_requirement_spec": {
        "categories": [
          {
            "category": "ENVIRONMENT",
            "requirements": [
              {
                "requirement_id": "req-max-wind-gust",
                "expr": "MAX_WIND_GUST(28mph)",
                "keyword": "MAX_WIND_GUST",
                "params": ["28mph"],
                "applicable_scopes": ["UAV"]
              }
            ]
          }
        ]
      },
      "retry": {
        "force_decision": "APPROVED"
      }
    }
  },
  "declared_payload": {
    "total_weight_kg": 2.5,
    "components": [
      {
        "type": "CAMERA_01"
      }
    ]
  },
  "requested_operation": {
    "operation_type": "INSPECTION",
    "priority": "NORMAL"
  }
}
```

SafeCert testing hook:

1. When `force_decision` is `ACTION_REQUIRED`, `test_overrides.decision_maker.retry.force_decision` is required and defines the forced result for the subsequent `RETRY` evaluation.
2. The Decision Maker stub also accepts `test_overrides.decision_maker.evidence_requirement_spec.categories`. Omit the spec to use the stub default.
3. A supplied custom spec must contain nonempty categories and requirements. Each requirement needs a unique `requirement_id`, nonempty `expr` and `keyword`, and one or more `applicable_scopes` values from `PILOT` and `UAV`.
4. This is useful for the SafeCert team to test different requirement sets without changing SADE code.
5. The test author supplies Decision Maker-owned requirement fields in an override. `requirement_id` is an opaque key unique within that spec, not a database row ID or a globally fixed certificate-type ID.

Environmental testing hook:

1. `test_overrides.weather_service.forecast` may be provided on the entry request.
2. In local/dev flows, the no-op environmental service will use that supplied forecast instead of its default hardcoded values.
3. This is useful for end-to-end testing that wants deterministic environmental context without changing SADE code.

Flight-monitor testing hook:

1. `test_overrides.flight_monitor` may be provided on the entry request.
2. On approval, SADE forwards that object as the outbound Flight Monitor `test_overrides` value.
3. When that object is present, Flight Monitor uses the test finalization path and closes the session automatically after a short delay.
4. If `test_overrides.flight_monitor` is absent, SADE forwards outbound `test_overrides=null`.
5. This is intentionally a pass-through hook for stub/dev integrations, so SADE does not interpret the object contents.

## 4) Action-required continuation is SafeCert-owned (manual for now)

This stage is from the SafeCert system perspective, not the pilot/operator UI perspective.

Normal production intent:

1. SADE emits an evidence requirement (`request_id`) to SafeCert.
2. SafeCert evaluates requirements and sends `POST /attestation-submission`.
3. SafeCert sets `in_response_to` to that same `request_id`.

Current environment status:

1. SADE can write outbound SafeCert requests to its internal outbox.
2. If `SAFECERT_OUTBOX_TRANSPORT=safecert_http` and the outbox worker has `OUTBOX_SAFECERT_URL` plus client cert/key secrets, SADE delivers the evidence requirement over HTTP.
3. Without `SAFECERT_OUTBOX_TRANSPORT`, SADE persists the request locally and you must send `/attestation-submission` manually to complete an action-required transaction.
4. For manual testing, get `action_required.action_id` from the entry status response and use that as `in_response_to`.

Operational reason:

1. This continuation is intentionally detached from the original entry HTTP request.
2. Once human review or document collection is involved, the elapsed time is no longer predictable.
3. The operator should therefore treat the status URL as the source of truth for ongoing progress, not the original `POST /entry-request` response or MQTT summary.
4. SADE also rejects overlapping windows for the same drone or same pilot, even before decisioning finishes.

## 5) Session finalization is Flight Monitor-owned

This stage is from the telemetry monitor/tracker perspective, not the pilot/operator UI perspective.

Current behavior:

1. SADE registers the approved session with the Flight Monitor.
2. If the operator wants to leave early, they may send `POST /exit-request`.
3. SADE accepts the request and queues it to Flight Monitor.
4. Flight Monitor honors the early-exit request by starting closeout and waiting for telemetry silence.
5. After the silence grace period, Flight Monitor closes the session with observed timestamps, summary, and events.
6. If telemetry keeps arriving, Flight Monitor waits until the drone goes silent rather than cutting off a still-transmitting session.
7. For no-drone integration tests, include `test_overrides.flight_monitor` on the entry request so Flight Monitor can close the session automatically.

Why this design exists:

1. Final closeout is based on telemetry-truth (actual observations), not only operator/operator-app intent.
2. `POST /exit-request` starts the early-exit closeout path, but the final recorded end still comes from Flight Monitor.
3. Operators should treat entry status and reputation records as the client-facing source of truth after Flight Monitor closes the session.
